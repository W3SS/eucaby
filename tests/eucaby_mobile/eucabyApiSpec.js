'use strict';

describe('eucaby api tests', function(){
    var $scope, $window, $httpBackend, OpenFB, $q, EucabyApi;
    var storage = {};
    var FB_PROFILE = {
        data: {
            first_name: 'Test', last_name: 'User', verified: true,
            name: 'Test User', locale: 'en_US', gender: 'male',
            email: 'test@example.com', id: 123,
            link: 'https://www.facebook.com/app_scoped_user_id/12345/',
            timezone: -8, updated_time: '2014-12-06T21:31:50+0000'
    }};
    var EC_AUTH = {
        access_token: 'AABBCC',
        expires_in: 2592000,
        refresh_token: 'ABCABC',
        scope: 'profile history location',
        token_type: 'Bearer'
    }
    var ENDPOINT = 'http://api.eucaby-dev.appspot.com';

    beforeEach(module('eucaby.api'));
    beforeEach(inject(function($rootScope, _$window_, _$httpBackend_, _$q_, _OpenFB_, _EucabyApi_){
        $scope = $rootScope.$new();
        $httpBackend = _$httpBackend_;
        $window = _$window_;
        $q = _$q_;
        OpenFB = _OpenFB_;
        EucabyApi = _EucabyApi_;
    }));
    beforeEach(function(){
        // LocalStorage mock.
        spyOn($window.localStorage, 'getItem').and.callFake(function(key) {
            return storage[key];
        });
        Object.defineProperty(sessionStorage, 'setItem', { writable: true });
        spyOn($window.localStorage, 'setItem').and.callFake(function(key, value) {
            storage[key] = value;
        });
    });
    beforeEach(function(){
        EucabyApi.init($window.localStorage);
    });

    afterEach(function(){
       storage = {};
    });

    it('should return error when fb auth fails', function(){
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?error=some_error#');
        };
        EucabyApi.login().then(null, function(data){
            expect(angular.equals(data, {error: 'some_error'})).toBe(true);
        });
        $scope.$digest();
    });

    it('should return error when fb profile request fails', function(){
        var deferredGet = $q.defer();
        // Facebook authenticated succeeded
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?#access_token=some_token');
        };
        OpenFB.get = function(){
            return deferredGet.promise;
        };
        // Failed to get Facebook profile
        deferredGet.reject('FB profile error');
        EucabyApi.login().then(null, function(data){
            expect(data).toBe('FB profile error');
        });
        $scope.$digest();
        // Key fbtoken has to be set
        expect($window.localStorage.fbtoken).toBe('some_token');
    });

    it('should return error when eucaby auth fails', function(){
        var deferredGet = $q.defer();
        var authError = {error: 'Server error'};
        // Facebook authenticated succeeded
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?#access_token=some_token');
        };
        OpenFB.get = function(){
            return deferredGet.promise;
        };
        // Facebook profile succeeded
        deferredGet.resolve(FB_PROFILE);
        $httpBackend.whenPOST(ENDPOINT + '/oauth/token').respond(500, authError);
        $httpBackend.expectPOST(ENDPOINT + '/oauth/token').respond(500, authError);
        EucabyApi.login().then(null, function(data){
            expect(angular.equals(data, authError)).toBe(true);
        });
        $scope.$digest();
        $httpBackend.flush();
        // Key fbtoken has to be set
        expect($window.localStorage.fbtoken).toBe('some_token');
    });

    it('should successfully login', function(){
        var deferredGet = $q.defer();
        // Facebook authenticated succeeded
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?#access_token=some_token');
        };
        OpenFB.get = function(){
            return deferredGet.promise;
        };
        // Facebook profile succeeded
        deferredGet.resolve(FB_PROFILE);
        $httpBackend.whenPOST(ENDPOINT + '/oauth/token').respond(EC_AUTH);
        $httpBackend.expectPOST(ENDPOINT + '/oauth/token').respond(EC_AUTH);
        EucabyApi.login().then(function(data){
            expect(angular.equals(data, EC_AUTH)).toBe(true);
        }, null);
        $scope.$digest();
        $httpBackend.flush();
        expect($window.localStorage.getItem('ec_access_token')).toBe('AABBCC');
        expect($window.localStorage.getItem('ec_refresh_token')).toBe('ABCABC');
        expect($window.localStorage.fbtoken).toBe(undefined);
    });
});