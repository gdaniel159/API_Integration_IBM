## Deployment

To deploy the project, follow these steps:

### 1. Local Server

```bash
  python app.py
```

### 2. Expose Local Server

```bash
  ngrok http 5000
```

### 3. Setup de la url

Once the server is deployed, you need to use the API endpoint at url/bot to access the chatbot features. In my case, I used NGROK to expose my local project route and then used the provided endpoint, assigning it to a service, such as Twilio.

![Logo](img_twilo_reference.png)

## Author

- [@gdaniel159](https://www.github.com/gdaniel159)
