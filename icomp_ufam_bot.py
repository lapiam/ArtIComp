import os
from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
import tensorflow as tf

# Load compressed models from tensorflow_hub
os.environ['TFHUB_MODEL_LOAD_FORMAT'] = 'COMPRESSED'

import tensorflow_hub as hub
# hub_model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/1')
hub_model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')

# Create the application instance with the Telegram bot token
# app = ApplicationBuilder().token("7825824681:AAEVnQiWFpZC3dZEjaCTBF0RJqEkZ-poEfU").build()
app = ApplicationBuilder() \
    .token("your telegram token") \
    .connect_timeout(30) \
    .read_timeout(30) \
    .build()

def tf2PIL(stylized_image):
    img_array = tf.squeeze(stylized_image).numpy()  # Remove batch dimension
    img_array = (img_array * 255).astype('uint8')  # Convert to 8-bit format
    return Image.fromarray(img_array)

def load_img(path_to_img):
    """
    Define a function to load an image and limit its maximum dimension to 512 pixels.
    """
    img = tf.io.read_file(path_to_img)
    img = tf.image.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    shape = tf.cast(tf.shape(img)[:-1], tf.float32)
    long_dim = max(shape)
    scale = 512 / long_dim # max_dim = 512
    new_shape = tf.cast(shape * scale, tf.int32)
    img = tf.image.resize(img, new_shape)
    img = img[tf.newaxis, :]
    return img

andinsky_style = load_img('wassily_andinsky.jpg')
van_gogh_style = load_img('van_gogh_2.jpg')
frida_style = load_img('frida_kahlo_2.jpg')
benito_style = load_img('benito.jpg')
hokusai_style = load_img('hokusai.jpg')

def preprocess_image(photo_bytes):
    """
    Load the content photo directly from bytes using TensorFlow and preprocess it.
    """
    content_image = tf.image.decode_image(photo_bytes, channels=3)
    content_image = tf.image.convert_image_dtype(content_image, tf.float32)
    shape = tf.cast(tf.shape(content_image)[:-1], tf.float32)
    long_dim = max(shape)
    scale = 512 / long_dim
    new_shape = tf.cast(shape * scale, tf.int32)
    content_image = tf.image.resize(content_image, new_shape)
    content_image = content_image[tf.newaxis, :]
    return content_image

def apply_TF_style(estilo, content_image):
    """ 
        Apply the style transfer using the TensorFlow Hub model
    """
    if estilo == 'van_gogh':
        stylized_image = hub_model(tf.constant(content_image), tf.constant(van_gogh_style))[0]
    elif estilo == 'frida':
        stylized_image = hub_model(tf.constant(content_image), tf.constant(frida_style))[0]
    elif estilo == 'andinsky':
        stylized_image = hub_model(tf.constant(content_image), tf.constant(andinsky_style))[0]
    elif estilo == 'benito':
        stylized_image = hub_model(tf.constant(content_image), tf.constant(benito_style))[0]
    elif estilo == 'hokusai':
        stylized_image = hub_model(tf.constant(content_image), tf.constant(hokusai_style))[0]
    return stylized_image

def apply_style(estilo, content_image):
    """ 
        Apply the style transfer using the TensorFlow Hub model and retunr the BytesIO object
    """
    stylized_image = apply_TF_style(estilo, content_image)
    stylized_pil_image = tf2PIL(stylized_image) # Convert the stylized TensorFlow image back to a PIL image
    output = BytesIO() # Save the stylized image to a BytesIO object
    stylized_pil_image.save(output, format='JPEG')
    output.seek(0)
    return output

message_1 = ("Olá! Eu sou um artista digital criado com Inteligência Artificial pelo Instituto de Computação da Universidade Federal do Amazonas.\n"
             "\nCompartilha uma foto comigo que eu vou pintar igual a um pintor famoso! ;p \n")

message_2 = ("Agora escolha um estilo:\n\n/van_gogh\n\n/frida\n\n/andinsky\n\n/benito\n\n/hokusai\n"
             "\nVc também pode enviar o comando '/estilos' para verificar as pinturas dos artitas fomosos.")

message_3 = ('Escolha seu estilo preferido:\n\n/van_gogh\n\n/frida\n\n/andinsky\n\n/benito\n\n/hokusai')

message_4 = ("Gostou? ;)\n"
             "\nSe vc gostou do ArtIComp então nos de uma força e faça um post nas redes sociais marcando o IComp/UFAM e nosso bot!\n")

message_5 = ("Desculpe, eu não reconheço esse comando.")

message_6 = ("Não entendi sua mensagem. Por favor, envie uma foto para estilizar ou use o comando /start para recomeçar.")

message_7 = ("Por favor, envie uma foto antes de escolher um estilo.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_1)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the largest available size of the photo
    photo_file_id = update.message.photo[-1].file_id

    # Download the photo
    photo_file = await context.bot.get_file(photo_file_id)
    photo_bytes = requests.get(photo_file.file_path).content
    
    # Preprocess the content photo
    content_image = preprocess_image(photo_bytes)
    
    # Store the content image in user_data for later use
    context.user_data['content_image'] = content_image

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_2)

async def styles(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("van_gogh_2.jpg", 'rb'))
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Estilo Van Gogh! /van_gogh')
    
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("frida_kahlo_2.jpg", 'rb'))
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Estilo Frida Kahlo! /frida')
    
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("wassily_andinsky.jpg", 'rb'))
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Estilo Wassily Andinsky! /andinsky')
    
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("benito.jpg", 'rb'))
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Estilo Benito Quinquel Martín! /benito')

    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("hokusai.jpg", 'rb'))
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Estilo Katsushika Hokusai! /hokusai')

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_3)

async def van_gogh(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    # Check if the user has uploaded a photo
    if 'content_image' not in context.user_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_7)
        return

    context.user_data['estilo'] = 'van_gogh'
    await context.bot.send_message(chat_id=update.effective_chat.id, text= f"Perfeito!\nVc escolheu o artista holandês Van Gogh.\nProcessando....")

    # Send back the stylized photo
    await context.bot.send_photo(chat_id=update.effective_chat.id, 
                                 photo=apply_style(context.user_data.get('estilo'), 
                                                      context.user_data.get('content_image')))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_4)

async def frida(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    # Check if the user has uploaded a photo
    if 'content_image' not in context.user_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_7)
        return

    context.user_data['estilo'] = 'frida'
    await context.bot.send_message(chat_id=update.effective_chat.id, text= f"Perfeito!\nVc escolheu a artista mexicana Frida Kahlo.\nProcessando....")

    # Send back the stylized photo
    await context.bot.send_photo(chat_id=update.effective_chat.id, 
                                 photo=apply_style(context.user_data.get('estilo'), 
                                                      context.user_data.get('content_image')))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_4)

async def andinsky(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    # Check if the user has uploaded a photo
    if 'content_image' not in context.user_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_7)
        return

    context.user_data['estilo'] = 'andinsky'
    await context.bot.send_message(chat_id=update.effective_chat.id, text= f"Perfeito!\nVc escolheu o artista russo-alemão Wassily Andinsky.\nProcessando....")

    # Send back the stylized photo
    await context.bot.send_photo(chat_id=update.effective_chat.id, 
                                 photo=apply_style(context.user_data.get('estilo'), 
                                                      context.user_data.get('content_image')))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_4)

async def benito(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    # Check if the user has uploaded a photo
    if 'content_image' not in context.user_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_7)
        return

    context.user_data['estilo'] = 'benito'
    await context.bot.send_message(chat_id=update.effective_chat.id, text= f"Perfeito!\nVc escolheu o artista argentino Benito Quinquela Martín.\nProcessando....")

    # Send back the stylized photo
    await context.bot.send_photo(chat_id=update.effective_chat.id, 
                                 photo=apply_style(context.user_data.get('estilo'), 
                                                      context.user_data.get('content_image')))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_4)

async def hokusai(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    # Check if the user has uploaded a photo
    if 'content_image' not in context.user_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_7)
        return

    context.user_data['estilo'] = 'hokusai'
    await context.bot.send_message(chat_id=update.effective_chat.id, text= f"Perfeito!\nVc escolheu o artista japonês Katsushika Hokusai.\nProcessando....")

    # Send back the stylized photo
    await context.bot.send_photo(chat_id=update.effective_chat.id, 
                                 photo=apply_style(context.user_data.get('estilo'), 
                                                      context.user_data.get('content_image')))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_4)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user if necessary."""
    if isinstance(context.error, NetworkError) or isinstance(context.error, TimedOut):
        # Handle the network error appropriately
        print(f"Network error occurred: {context.error}")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unrecognized commands."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_5)

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any other messages that are not commands."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_6)

# Handle network issues
app.add_error_handler(error_handler)

# Add handlers to respond to commands or photo messages
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('estilos', styles))
app.add_handler(CommandHandler('van_gogh', van_gogh))
app.add_handler(CommandHandler('frida', frida))
app.add_handler(CommandHandler('andinsky', andinsky))
app.add_handler(CommandHandler('benito', benito))
app.add_handler(CommandHandler('hokusai', hokusai))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# Add a MessageHandler to handle unrecognized commands
app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

# Add a MessageHandler to handle random text messages
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))

app.run_polling()