Welcome to the RM Life Planner Backend. Hosted by Hostinger.com, and running on a FastAPI server
paired with a MySQL database, it provides laser-fast access to tha critical data used by the RM
Life Planner IOS application, found at:
     https://github.com/spencerjchavez/RM-Life-Planner-Frontend

All passwords are hashed with py-bcrypt and securely stored. No information can be retrieved by the server
without first providing valid user credentials, and then supplying the generated api_key with each subsequent API request.
In an effort to protect user data, API keys are only valid for a limited period of time until a login is required again.
As we approach our official launch, 2-factor authentication will likely be required to use our services.


Find API documentation at:
http://191.101.1.153/docs

All endpoints are accessed at http://191.101.1.153
