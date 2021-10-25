from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters
import wikipedia as wiki 

# put your toen here
BOT_TOKEN= "2069891105:AAGUAkzP0NfitI5wzCQA6P_RzQDLbtab8YY"

updater= Updater(BOT_TOKEN)  #Bot Token is given by BotFather on Telegram while creating bot. 

def get_wiki(word):
    try:
        return wiki.summary(word)
    except:
        return "Not Found"

def textpro(bot, update):
    msg= update.message.text.lower()
    senderName= update.message.from_user.first_name
    chatid= update.message.chat.id
    print("{}: {}".format(senderName, msg))
    if(msg.startswith('wiki')):
        bot.send_message(chat_id= chatid,text= get_wiki(msg[5:]))
        print("Bot: Wikipedia summery of {}".format(msg[5:]))
    else:
        bot.send_message(chat_id= chatid, text= "{}, Invalid command".format(senderName))
        print("Bot: Invalid command")

updater.dispatcher.add_handler(MessageHandler(Filters.text, textpro))
updater.start_polling()
print("Bot Server Started")
updater.idle()
#DONE
