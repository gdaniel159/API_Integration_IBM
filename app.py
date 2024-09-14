from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
import requests

app = Flask(__name__)
app.secret_key = 'pKUoKNQm88'

API_KEY = "YOUR_IBM_API_KEY"

# Obtén el token de autenticación del modelo de IBM
# Get the authentication token from the IBM model.

def get_ibm_token():
    response = requests.post(
        'https://iam.cloud.ibm.com/identity/token',
        data={"apikey": API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'}
    )
    return response.json()["access_token"]

# Función para hacer la predicción
def get_prediction(values):
    token = get_ibm_token()
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}

    payload_scoring = {
        "input_data": [
            {
                "fields": [
                    "age", "sex", "blood_pressure", "cholesterol", "bmi", 
                    "fasting_blood_sugar", "physical_activity", "smoking", 
                    "alcohol_consumption", "diet", "stress_level", 
                    "family_history", "resting_heart_rate", "daily_activity_level"
                ],
                "values": [values]
            }
        ]
    }

    # El endpoint modificarlo por el ya existente en tu entorno con tu propio modelo ya entrenado en IBM MACHINE LEARNING

    # Modify the endpoint to use the one already existing in your environment with your own pre-trained model in IBM MACHINE LEARNING.

    response = requests.post(
        'https://us-south.ml.cloud.ibm.com/ml/v4/deployments/0a873bc8-28e6-40e1-8224-2c2a34b47ac0/predictions?version=2021-05-01', 
        json=payload_scoring,
        headers=headers
    )
    return response.json()

# Validaciones por tipo de dato esperado
# Validations by Expected Data Type

def validate_input(answer, question_index):
    # Tipos de datos esperados por pregunta
    # Expected Data Types by Question
    expected_types = [
        int,    # Edad
        int,    # Sexo (0 o 1)
        int,    # Presión arterial
        int,    # Colesterol
        float,  # BMI
        int,    # Azúcar en ayunas (0 o 1)
        int,    # Actividad física (1 a 3)
        int,    # Fumar (0 o 1)
        int,    # Alcohol (0 o 1)
        int,    # Dieta (0 o 1)
        int,    # Nivel de estrés (1 a 10)
        int,    # Historial familiar (0 o 1)
        int,    # Ritmo cardíaco en reposo
        int,    # Actividad diaria (1 a 3)
    ]

    try:
        if question_index < len(expected_types):
            if expected_types[question_index] == int:
                return int(answer)
            elif expected_types[question_index] == float:
                return float(answer)
        return answer
    except ValueError:
        return None

def handle_prediction():
    # Extrae respuestas enviadas al modelo de predicción
    # Extract responses sent to the prediction model.
    print("Answers being sent to prediction model:", session['answers'])

    # Obtiene el resultado de la predicción
    # Obtain the prediction result.
    prediction_result = get_prediction(session['answers'])
    print("Full prediction result:", prediction_result)

    # Inicializa la variable de mensajes
    # Initialize the message variable
    messages = []

    # Verifica la estructura del resultado de la predicción
    # Verify the structure of the prediction result.
    if 'predictions' in prediction_result and len(prediction_result['predictions']) > 0:
        values = prediction_result['predictions'][0]['values']
        print("Values extracted from prediction result:", values)
        
        if len(values) > 0 and len(values[0]) > 1:
            probabilities = values[0][1]
            print("Probabilities extracted:", probabilities)

            # Verifica si hay al menos dos probabilidades y determina el riesgo
            # Check if there are at least two probabilities and determine the risk.
            if len(probabilities) > 1:
                probability = probabilities[1]
                if probability > 0.5:
                    messages.append(f"Es probable que tengas un riesgo de enfermedad cardíaca. Probabilidad: {probability:.2%}")
                else:
                    messages.append(f"No parece que tengas un alto riesgo de enfermedad cardíaca. Probabilidad: {probability:.2%}")
            else:
                messages.append("Lo siento, no pude interpretar el resultado de la predicción correctamente.")
        else:
            messages.append("Lo siento, no pude interpretar el resultado de la predicción correctamente.")
    else:
        messages.append("Lo siento, hubo un problema al obtener la predicción.")

    # Mensaje adicional para reiniciar la evaluación
    # messages.append("¿Te gustaría reiniciar la evaluación? Responde 'sí' para comenzar de nuevo o 'no' para terminar.")

    # Devuelve la lista de mensajes como un solo string
    # Return the list of messages as a single string.
    
    return "\n".join(messages)

# Ruta para recibir mensajes de WhatsApp
# Route to receive WhatsApp messages

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip().lower()
    response = MessagingResponse()
    message = response.message()

    # Maneja la selección de opciones inicial
    # Handle the initial option selection.
    if 'step' not in session:
        return init_options()  # This will now correctly return the initial options

    # Opciones iniciales
    # Initial options

    if session['step'] == 'options':
        if incoming_msg == '1':
            message.body("Nuestro horario de atención es de lunes a viernes, de 9:00 AM a 6:00 PM.")
            session.clear()
        elif incoming_msg == '2':
            return init_questions()
        else:
            message.body("Por favor selecciona una opción válida (1 o 2).")
        return str(response)

    # Cuestionario de evaluación
    # Evaluation questionnaire
    if 'questions' in session:
        if 'current_question' in session and session['current_question'] < len(session['questions']):
            current_question_index = session['current_question']
            validated_answer = validate_input(incoming_msg, current_question_index)

            if validated_answer is not None:
                session['answers'].append(validated_answer)
                session['current_question'] += 1

                if session['current_question'] < len(session['questions']):
                    message.body(session['questions'][session['current_question']])
                else:
                    response_handle = handle_prediction()
                    message.body(response_handle)
                    session.clear()  # Reinicia la sesión después de completar las preguntas # Restart the session after completing the questions.

            else:
                message.body(f"Por favor, proporciona un valor válido para la pregunta: {session['questions'][current_question_index]}")
        return str(response)

    return str(response)


def init_options():
    response = MessagingResponse()  # Create an instance of MessagingResponse
    message = response.message()  # Now call message() on the instance
    
    options = [
        "1) ¿Cuál es el horario de atención?",
        "2) ¿Deseas saber si puedes padecer de una enfermedad cardíaca?"
    ]

    message.body("\n".join(options))
    session['step'] = 'options'

    return str(response)


def init_questions():
    response = MessagingResponse()
    message = response.message()
    
    session['questions'] = [
        "¿Cuál es tu edad?",
        "¿Cuál es tu sexo? (0 para femenino, 1 para masculino)",
        "¿Cuál es tu presión arterial?",
        "¿Cuál es tu nivel de colesterol?",
        "¿Cuál es tu índice de masa corporal (BMI)?",
        "¿Nivel de azúcar en ayunas? (0 para normal, 1 para alto)",
        "¿Nivel de actividad física? (1 a 3, siendo 1 bajo y 3 alto)",
        "¿Fumas? (0 para no, 1 para sí)",
        "¿Consumes alcohol? (0 para no, 1 para sí)",
        "¿Cómo es tu dieta? (0 para poco saludable, 1 para saludable)",
        "¿Nivel de estrés? (1 a 10)",
        "¿Tienes historial familiar de enfermedades cardíacas? (0 para no, 1 para sí)",
        "¿Cuál es tu ritmo cardíaco en reposo?",
        "¿Nivel de actividad diaria? (1 a 3, siendo 1 bajo y 3 alto)"
    ]
    session['answers'] = []
    session['current_question'] = 0
    message.body("¡Hola! Te haré algunas preguntas para evaluar tu riesgo cardíaco. " + session['questions'][0])
    session['step'] = 'questions'
    return str(response)

if __name__ == '__main__':
    app.run(debug=True)