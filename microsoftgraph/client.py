from __future__ import absolute_import
import base64
import mimetypes
import requests
import json
from microsoftgraph import exceptions
from microsoftgraph.decorators import token_required
from urllib import urlencode, quote_plus
from io import open
from urlparse import urlparse


class Client(object):
    AUTHORITY_URL = u'https://login.microsoftonline.com/'
    AUTH_ENDPOINT = u'/oauth2/v2.0/authorize?'
    TOKEN_ENDPOINT = u'/oauth2/v2.0/token'
    RESOURCE = u'https://graph.microsoft.com/'

    OFFICE365_AUTHORITY_URL = u'https://login.live.com'
    OFFICE365_AUTH_ENDPOINT = u'/oauth20_authorize.srf?'
    OFFICE365_TOKEN_ENDPOINT = u'/oauth20_token.srf'

    def __init__(self, client_id, client_secret, api_version=u'v1.0', account_type=u'common', office365=False):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_version = api_version
        self.account_type = account_type

        self.base_url = self.RESOURCE + self.api_version + u'/'
        self.token = None
        self.office365 = office365
        self.office365_token = None

    def authorization_url(self, redirect_uri, scope, state=None):
        u"""

        Args:
            redirect_uri: The redirect_uri of your app, where authentication responses can be sent and received by
            your app.  It must exactly match one of the redirect_uris you registered in the app registration portal

            scope: A list of the Microsoft Graph permissions that you want the user to consent to. This may also
            include OpenID scopes.

            state: A value included in the request that will also be returned in the token response.
            It can be a string of any content that you wish.  A randomly generated unique value is typically
            used for preventing cross-site request forgery attacks.  The state is also used to encode information
            about the user's state in the app before the authentication request occurred, such as the page or view
            they were on.

        Returns:
            A string.

        """
        params = {
            u'client_id': self.client_id,
            u'redirect_uri': redirect_uri,
            u'scope': u' '.join(scope),
            u'response_type': u'code',
            u'response_mode': u'query'
        }

        if state:
            params[u'state'] = None
        if self.office365:
            response = self.OFFICE365_AUTHORITY_URL + self.OFFICE365_AUTH_ENDPOINT + urlencode(params)
        else:
            response = self.AUTHORITY_URL + self.account_type + self.AUTH_ENDPOINT + urlencode(params)
        return response

    def exchange_code(self, redirect_uri, code):
        u"""Exchanges a code for a Token.

        Args:
            redirect_uri: The redirect_uri of your app, where authentication responses can be sent and received by
            your app.  It must exactly match one of the redirect_uris you registered in the app registration portal

            code: The authorization_code that you acquired in the first leg of the flow.

        Returns:
            A dict.

        """
        data = {
            u'client_id': self.client_id,
            u'redirect_uri': redirect_uri,
            u'client_secret': self.client_secret,
            u'code': code,
            u'grant_type': u'authorization_code',
        }
        if self.office365:
            response = requests.post(self.OFFICE365_AUTHORITY_URL + self.OFFICE365_TOKEN_ENDPOINT, data=data)
        else:
            response = requests.post(self.AUTHORITY_URL + self.account_type + self.TOKEN_ENDPOINT, data=data)
        return self._parse(response)

    def refresh_token(self, redirect_uri, refresh_token):
        u"""

        Args:
            redirect_uri: The redirect_uri of your app, where authentication responses can be sent and received by
            your app.  It must exactly match one of the redirect_uris you registered in the app registration portal

            refresh_token: An OAuth 2.0 refresh token. Your app can use this token acquire additional access tokens
            after the current access token expires. Refresh tokens are long-lived, and can be used to retain access
            to resources for extended periods of time.

        Returns:
            A dict.

        """
        data = {
            u'client_id': self.client_id,
            u'redirect_uri': redirect_uri,
            u'client_secret': self.client_secret,
            u'refresh_token': refresh_token,
            u'grant_type': u'refresh_token',
        }
        if self.office365:
            response = requests.post(self.OFFICE365_AUTHORITY_URL + self.OFFICE365_TOKEN_ENDPOINT, data=data)
        else:
            response = requests.post(self.AUTHORITY_URL + self.account_type + self.TOKEN_ENDPOINT, data=data)
        return self._parse(response)

    def set_token(self, token):
        u"""Sets the Token for its use in this library.

        Args:
            token: A string with the Token.

        """
        if self.office365:
            self.office365_token = token
        else:
            self.token = token

    @token_required
    def get_me(self, params=None):
        u"""Retrieve the properties and relationships of user object.

        Note: Getting a user returns a default set of properties only (businessPhones, displayName, givenName, id,
        jobTitle, mail, mobilePhone, officeLocation, preferredLanguage, surname, userPrincipalName).
        Use $select to get the other properties and relationships for the user object.

        Args:
            params: A dict.

        Returns:
            A dict.

        """
        return self._get(self.base_url + u'me', params=params)

    @token_required
    def get_message(self, message_id, params=None):
        u"""Retrieve the properties and relationships of a message object.

        Args:
            message_id: A dict.
            params:

        Returns:
            A dict.

        """
        return self._get(self.base_url + u'me/messages/' + message_id, params=params)

    @token_required
    def create_subscription(self, change_type, notification_url, resource, expiration_datetime, client_state=None):
        u"""Creating a subscription is the first step to start receiving notifications for a resource.

        Args:
            change_type: The event type that caused the notification. For example, created on mail receive, or updated
            on marking a message read.
            notification_url:
            resource: The URI of the resource relative to https://graph.microsoft.com.
            expiration_datetime: The expiration time for the subscription.
            client_state: The clientState property specified in the subscription request.

        Returns:
            A dict.

        """
        data = {
            u'changeType': change_type,
            u'notificationUrl': notification_url,
            u'resource': resource,
            u'expirationDateTime': expiration_datetime,
            u'clientState': client_state
        }
        return self._post(u'https://graph.microsoft.com/beta/' + u'subscriptions', json=data)

    @token_required
    def renew_subscription(self, subscription_id, expiration_datetime):
        u"""The client can renew a subscription with a specific expiration date of up to three days from the time
        of request. The expirationDateTime property is required.


        Args:
            subscription_id:
            expiration_datetime:

        Returns:
            A dict.

        """
        data = {
            u'expirationDateTime': expiration_datetime
        }
        return self._patch(u'https://graph.microsoft.com/beta/' + u'subscriptions/{}'.format(subscription_id), json=data)

    @token_required
    def delete_subscription(self, subscription_id):
        u"""The client can stop receiving notifications by deleting the subscription using its ID.

        Args:
            subscription_id:

        Returns:
            None.

        """
        return self._delete(u'https://graph.microsoft.com/beta/' + u'subscriptions/{}'.format(subscription_id))

    # Onenote
    @token_required
    def list_notebooks(self):
        u"""Retrieve a list of notebook objects.

        Returns:
            A dict.

        """
        return self._get(self.base_url + u'me/onenote/notebooks')

    @token_required
    def get_notebook(self, notebook_id):
        u"""Retrieve the properties and relationships of a notebook object.

        Args:
            notebook_id:

        Returns:
            A dict.

        """
        return self._get(self.base_url + u'me/onenote/notebooks/' + notebook_id)

    @token_required
    def get_notebook_sections(self, notebook_id):
        u"""Retrieve the properties and relationships of a notebook object.

        Args:
            notebook_id:

        Returns:
            A dict.

        """
        return self._get(self.base_url + u'me/onenote/notebooks/{}/sections'.format(notebook_id))

    @token_required
    def create_page(self, section_id, files):
        u"""Create a new page in the specified section.

        Args:
            section_id:
            files:

        Returns:
            A dict.

        """
        return self._post(self.base_url + u'/me/onenote/sections/{}/pages'.format(section_id), files=files)

    @token_required
    def list_pages(self, params=None):
        u"""Create a new page in the specified section.

        Args:
            params:

        Returns:
            A dict.

        """
        return self._get(self.base_url + u'/me/onenote/pages', params=params)

    # Calendar
    @token_required
    def get_me_events(self):
        u"""Get a list of event objects in the user's mailbox. The list contains single instance meetings and
        series masters.

        Currently, this operation returns event bodies in only HTML format.

        Returns:
            A dict.

        """
        return self._get(self.base_url + u'me/events')

    @token_required
    def create_calendar_event(self, subject, content, start_datetime, start_timezone, end_datetime, end_timezone,
                              location, calendar=None, **kwargs):
        u"""
        Create a new calendar event.

        Args:
            subject: subject of event, string
            content: content of event, string
            start_datetime: in the format of 2017-09-04T11:00:00, dateTimeTimeZone string
            start_timezone: in the format of Pacific Standard Time, string
            end_datetime: in the format of 2017-09-04T11:00:00, dateTimeTimeZone string
            end_timezone: in the format of Pacific Standard Time, string
            location:   string
            attendees: list of dicts of the form:
                        {"emailAddress": {"address": a['attendees_email'],"name": a['attendees_name']}
            calendar:

        Returns:
            A dict.

        """
        # TODO: attendees
        # attendees_list = [{
        #     "emailAddress": {
        #         "address": a['attendees_email'],
        #         "name": a['attendees_name']
        #     },
        #     "type": a['attendees_type']
        # } for a in kwargs['attendees']]
        body = {
            u"subject": subject,
            u"body": {
                u"contentType": u"HTML",
                u"content": content
            },
            u"start": {
                u"dateTime": start_datetime,
                u"timeZone": start_timezone
            },
            u"end": {
                u"dateTime": end_datetime,
                u"timeZone": end_timezone
            },
            u"location": {
                u"displayName": location
            },
            # "attendees": attendees_list
        }
        url = u'me/calendars/{}/events'.format(calendar) if calendar is not None else u'me/events'
        return self._post(self.base_url + url, json=body)

    @token_required
    def create_calendar(self, name):
        u"""Create an event in the user's default calendar or specified calendar.

        You can specify the time zone for each of the start and end times of the event as part of these values,
        as the  start and end properties are of dateTimeTimeZone type.

        When an event is sent, the server sends invitations to all the attendees.

        Args:
            name:

        Returns:
            A dict.

        """
        body = {
            u'name': u'{}'.format(name)
        }
        return self._post(self.base_url + u'me/calendars', json=body)

    @token_required
    def get_me_calendars(self):
        u"""Get all the user's calendars (/calendars navigation property), get the calendars from the default
        calendar group or from a specific calendar group.

        Returns:
            A dict.

        """
        return self._get(self.base_url + u'me/calendars')

    # Mail
    @token_required
    def send_mail(self, subject=None, recipients=None, body=u'', content_type=u'HTML', attachments=None):
        u"""Helper to send email from current user.

        Args:
            subject: email subject (required)
            recipients: list of recipient email addresses (required)
            body: body of the message
            content_type: content type (default is 'HTML')
            attachments: list of file attachments (local filenames)

        Returns:
            Returns the response from the POST to the sendmail API.
        """

        # Verify that required arguments have been passed.
        if not all([subject, recipients]):
            raise ValueError(u'sendmail(): required arguments missing')

        # Create recipient list in required format.
        recipient_list = [{u'EmailAddress': {u'Address': address}} for address in recipients]

        # Create list of attachments in required format.
        attached_files = []
        if attachments:
            for filename in attachments:
                b64_content = base64.b64encode(open(filename, u'rb').read())
                mime_type = mimetypes.guess_type(filename)[0]
                mime_type = mime_type if mime_type else u''
                attached_files.append(
                    {u'@odata.type': u'#microsoft.graph.fileAttachment', u'ContentBytes': b64_content.decode(u'utf-8'),
                     u'ContentType': mime_type, u'Name': filename})

        # Create email message in required format.
        email_msg = {u'Message': {u'Subject': subject,
                                 u'Body': {u'ContentType': content_type, u'Content': body},
                                 u'ToRecipients': recipient_list,
                                 u'Attachments': attached_files},
                     u'SaveToSentItems': u'true'}

        # Do a POST to Graph's sendMail API and return the response.
        return self._post(self.base_url + u'me/microsoft.graph.sendMail', json=email_msg)

    # Outlook
    @token_required
    def outlook_get_me_contacts(self, data_id=None, params=None):
        if data_id is None:
            url = u"{0}me/contacts".format(self.base_url)
        else:
            url = u"{0}me/contacts/{1}".format(self.base_url, data_id)
        return self._get(url, params=params)

    @token_required
    def outlook_create_me_contact(self, **kwargs):
        url = u"{0}me/contacts".format(self.base_url)
        return self._post(url, **kwargs)

    @token_required
    def outlook_create_contact_in_folder(self, folder_id, **kwargs):
        url = u"{0}/me/contactFolders/{1}/contacts".format(self.base_url, folder_id)
        return self._post(url, **kwargs)

    @token_required
    def outlook_get_contact_folders(self, params=None):
        url = u"{0}me/contactFolders".format(self.base_url)
        return self._get(url, params=params)

    @token_required
    def outlook_create_contact_folder(self, **kwargs):
        url = u"{0}me/contactFolders".format(self.base_url)
        return self._post(url, **kwargs)

    # Onedrive
    @token_required
    def drive_root_items(self, params=None):
        return self._get(u'https://graph.microsoft.com/beta/me/drive/root', params=params)

    @token_required
    def drive_root_children_items(self, params=None):
        return self._get(u'https://graph.microsoft.com/beta/me/drive/root/children', params=params)

    @token_required
    def drive_specific_folder(self, folder_id, params=None):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/children".format(folder_id)
        return self._get(url, params=params)

    @token_required
    def drive_create_session(self, item_id, **kwargs):
        url = u"https://graph.microsoft.com/v1.0/me/drive/items/{0}/workbook/createSession".format(item_id)
        # url = "https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/createSession".format(item_id)
        return self._post(url, **kwargs)

    @token_required
    def drive_refresh_session(self, item_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/refreshSession".format(item_id)
        return self._post(url, **kwargs)

    @token_required
    def drive_close_session(self, item_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/closeSession".format(item_id)
        return self._post(url, **kwargs)

    # Excel
    @token_required
    def excel_get_worksheets(self, item_id, params=None, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets".format(item_id)
        return self._get(url, params=params, **kwargs)

    @token_required
    def excel_get_names(self, item_id, params=None, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/names".format(item_id)
        return self._get(url, params=params, **kwargs)

    @token_required
    def excel_add_worksheet(self, item_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/add".format(item_id)
        return self._post(url, **kwargs)

    @token_required
    def excel_get_specific_worksheet(self, item_id, worksheet_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}".format(item_id, quote_plus(worksheet_id))
        return self._get(url, **kwargs)

    @token_required
    def excel_update_worksheet(self, item_id, worksheet_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}".format(item_id, quote_plus(worksheet_id))
        return self._patch(url, **kwargs)

    @token_required
    def excel_get_charts(self, item_id, worksheet_id, params=None, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}/charts".format(item_id, quote_plus(worksheet_id))
        return self._get(url, params=params, **kwargs)

    @token_required
    def excel_add_chart(self, item_id, worksheet_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}/charts/add".format(item_id, quote_plus(worksheet_id))
        return self._post(url, **kwargs)

    @token_required
    def excel_get_tables(self, item_id, params=None, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/tables".format(item_id)
        return self._get(url, params=params, **kwargs)

    @token_required
    def excel_add_table(self, item_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/tables/add".format(item_id)
        return self._post(url, **kwargs)

    @token_required
    def excel_add_column(self, item_id, worksheets_id, table_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}/tables/{2}/columns".format(item_id, quote_plus(worksheets_id), table_id)
        return self._post(url, **kwargs)

    @token_required
    def excel_add_row(self, item_id, worksheets_id, table_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}/tables/{2}/rows".format(item_id, quote_plus(worksheets_id), table_id)
        return self._post(url, **kwargs)

    @token_required
    def excel_get_rows(self, item_id, table_id, params=None, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/tables/{1}/rows".format(item_id, table_id)
        return self._get(url, params=params, **kwargs)

    # @token_required
    # def excel_get_cell(self, item_id, worksheets_id, params=None, **kwargs):
    #     url = "https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}/Cell(row='1', column='A')".format(item_id, quote_plus(worksheets_id))
    #     return self._get(url, params=params, **kwargs)

    # @token_required
    # def excel_add_cell(self, item_id, worksheets_id, **kwargs):
    #     url = "https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}/rows".format(item_id, worksheets_id)
    #     return self._patch(url, **kwargs)

    @token_required
    def excel_get_range(self, item_id, worksheets_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}/range(address='A1:B2')".format(item_id, quote_plus(worksheets_id))
        return self._get(url, **kwargs)

    @token_required
    def excel_update_range(self, item_id, worksheets_id, **kwargs):
        url = u"https://graph.microsoft.com/beta/me/drive/items/{0}/workbook/worksheets/{1}/range(address='A1:B2')".format(item_id, quote_plus(worksheets_id))
        return self._patch(url, **kwargs)

    def _get(self, url, **kwargs):
        return self._request(u'GET', url, **kwargs)

    def _post(self, url, **kwargs):
        return self._request(u'POST', url, **kwargs)

    def _put(self, url, **kwargs):
        return self._request(u'PUT', url, **kwargs)

    def _patch(self, url, **kwargs):
        return self._request(u'PATCH', url, **kwargs)

    def _delete(self, url, **kwargs):
        return self._request(u'DELETE', url, **kwargs)

    def _request(self, method, url, headers=None, **kwargs):
        _headers = {
            u'Accept': u'application/json',
        }
        if self.office365:
            _headers[u'Authorization'] = u'Bearer ' + self.office365_token[u'access_token']
        else:
            _headers[u'Authorization'] = u'Bearer ' + self.token[u'access_token']
        if headers:
            _headers.update(headers)
        if u'files' not in kwargs:
            # If you use the 'files' keyword, the library will set the Content-Type to multipart/form-data
            # and will generate a boundary.
            _headers[u'Content-Type'] = u'application/json'
        return self._parse(requests.request(method, url, headers=_headers, **kwargs))

    def _parse(self, response):
        status_code = response.status_code
        if u'application/json' in response.headers[u'Content-Type']:
            r = response.json()
        else:
            r = response.text
        if status_code in (200, 201, 202):
            return r
        elif status_code == 204:
            return None
        elif status_code == 400:
            raise exceptions.BadRequest(r)
        elif status_code == 401:
            raise exceptions.Unauthorized(r)
        elif status_code == 403:
            raise exceptions.Forbidden(r)
        elif status_code == 404:
            raise exceptions.NotFound(r)
        elif status_code == 405:
            raise exceptions.MethodNotAllowed(r)
        elif status_code == 406:
            raise exceptions.NotAcceptable(r)
        elif status_code == 409:
            raise exceptions.Conflict(r)
        elif status_code == 410:
            raise exceptions.Gone(r)
        elif status_code == 411:
            raise exceptions.LengthRequired(r)
        elif status_code == 412:
            raise exceptions.PreconditionFailed(r)
        elif status_code == 413:
            raise exceptions.RequestEntityTooLarge(r)
        elif status_code == 415:
            raise exceptions.UnsupportedMediaType(r)
        elif status_code == 416:
            raise exceptions.RequestedRangeNotSatisfiable(r)
        elif status_code == 422:
            raise exceptions.UnprocessableEntity(r)
        elif status_code == 429:
            raise exceptions.TooManyRequests(r)
        elif status_code == 500:
            raise exceptions.InternalServerError(r)
        elif status_code == 501:
            raise exceptions.NotImplemented(r)
        elif status_code == 503:
            raise exceptions.ServiceUnavailable(r)
        elif status_code == 504:
            raise exceptions.GatewayTimeout(r)
        elif status_code == 507:
            raise exceptions.InsufficientStorage(r)
        elif status_code == 509:
            raise exceptions.BandwidthLimitExceeded(r)
        else:
            raise exceptions.UnknownError(r)
