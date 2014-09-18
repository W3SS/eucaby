#import settings
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from eucaby.core import models as core_models
from eucaby.api import services
from eucaby.api import messages as api_messages

package = 'Eucaby'


@endpoints.api(name='eucaby', version='v1')
class LocationApi(remote.Service):

    REQUEST_RESOURCE = endpoints.ResourceContainer(
        message_types.VoidMessage,
        sender_email=messages.StringField(1),
        receiver_email=messages.StringField(2))

    @endpoints.method(REQUEST_RESOURCE, api_messages.Session,
                      path='location/request', http_method='POST',
                      name='location.request')
    def request_location(self, request):
        session = core_models.Session.create(
            request.sender_email, request.receiver_email)
        #req = core_models.Request.create(session)

        return api_messages.Session(
            key=session.key, sender_email=session.sender_email,
            receiver_email=session.receiver_email)

application = endpoints.api_server([LocationApi], restricted=False)

