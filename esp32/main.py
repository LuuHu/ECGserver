
from machine import Pin, PWM, ADC, reset, RTC, Timer, I2C
import ssd1306
from icon import heart_icon, circle_icon

def screen_show(record=False,AES=False,trans=False,net=False,bpm=None,error=False,clear=False):
    if record==False and AES==False and trans==False and net==False and bpm==None and error==False:
        display.fill(1)
        display.show()
        return 1
    elif record:
        for y, row in enumerate(heart_icon):
            for x, c in enumerate(row):
                display.pixel(x+1, y+9, c)
    display.show()
    return 1

blue = Pin(2,Pin.OUT)
blue.value(1)

i2c = I2C(1,scl=Pin(22),sda=Pin(21))
display = ssd1306.SSD1306_I2C(128,32,i2c)


import network
import time
import ucryptolib
from uos import urandom
import urllib.urequest as request
import ujson

rtc = RTC
tim0 = Timer(-1)
tim1 = Timer(-1)

heartline = ''

adc0=ADC(Pin(32))
adc0.atten(ADC.ATTN_11DB)
adc0.width(ADC.WIDTH_12BIT)   

SSID="CMMMM0"
pwd="zc000000"
url= None #URL
key = 'This is the key!'

cvtTable = {0:'A',1:'B',2:'C',3:'D',4:'E',5:'F',6:'G',7:'H',8:'I',9:'J',10:'K',11:'L',12:'M',13:'N',14:'O',15:'P',16:'Q',17:'R',18:'S',19:'T',20:'U',21:'V',22:'W',23:'X',24:'Y',25:'Z',
            26:'a',27:'b',28:'c',29:'d',30:'e',31:'f',32:'g',33:'h',34:'i',35:'j',36:'k',37:'l',38:'m',39:'n',40:'o',41:'p',42:'q',43:'r',44:'s',45:'t',46:'u',47:'v',48:'w',49:'x',50:'y',51:'z',
            52:'0',53:'1',54:'2',55:'3',56:'4',57:'5',58:'6',59:'7',60:'8',61:'9',62:',',63:'.'}

int2code = lambda n: cvtTable[n//64] + cvtTable[n%64]
pad = lambda s: s + (16 - len(s) % 16) * chr(0)

def connectWIFI():
    blue.value(1)
    global SSID, pwd
    wlan=network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.disconnect()
    wlan.connect(SSID,pwd)
    ct = 0
    while(wlan.ifconfig()[0]=='0.0.0.0'):
        time.sleep(1)
        ct += 1
        if ct==30: error_report(0)
    blue.value(0)
    return True

def error_report(resumable=True):
    for t in range(10):
        blue.value(t%2)
        time.sleep_ms(500)
    if resumable:
        return 0
    reset()

def send(form):
    response = request.urlopen(url,data = form)
    print(response.read())

def get_adc():
    global tim0,tim1
    tim0.init(period=15000, mode=Timer.ONE_SHOT, callback=stop)
    tim1.init(period=2, mode=Timer.PERIODIC, callback=rec)
    time.sleep(12)
    
def rec(_):
    global heartline
    heartline += int2code(adc0.read())
    
def stop(_):
    global tim1,tim0
    tim1.deinit()
    tim0.deinit()
    
def encrypt(data):
    iv = urandom(16)
    print(iv)
    ecr = ucryptolib.aes(key, 2, iv)
    return iv+ecr.encrypt(pad(data))

time.sleep(1)
blue.value(0)



if __name__ == '__main__':
    connectWIFI()
    while True:
        show_herat_icon()
        get_adc()
        data = encrypt(heartline)
        heartline = ''
        send(data)
        print('sent')
    
