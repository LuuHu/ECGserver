
from machine import Pin, PWM, ADC, reset, RTC, Timer, I2C, UART
import ssd1306, network, time, ujson, ure, binascii
from umqtt.simple import MQTTClient

# define basic objects : screen, clock, led,adc
i2c = I2C(1,scl=Pin(23),sda=Pin(22))
display = ssd1306.SSD1306_I2C(128,32,i2c)
rtc = RTC
tim = Timer(-1)
blue = Pin(2,Pin.OUT)
riner_low = Pin(19,Pin.OUT)
riner_low.value(0)
riner_pwm = PWM(Pin(18), freq=550, duty=512)
riner_pwm.init()
adc0=ADC(Pin(32))
adc0.atten(ADC.ATTN_11DB)
adc0.width(ADC.WIDTH_12BIT)   

# define basic connetion info

nbiot_upload_addr = "http://sager.ga:888"
nbiot_upload_path = "/test"
#SSID="CQUPTHub"
#password="WXWL10000"

key = 'This is the key!'

url = 'a15f12ce46.iot-mqtts.cn-north-4.myhuaweicloud.com'
port = 1883

# define trans function
cvtTable = {0:'A',1:'B',2:'C',3:'D',4:'E',5:'F',6:'G',7:'H',8:'I',9:'J',10:'K',11:'L',12:'M',13:'N',14:'O',15:'P',16:'Q',17:'R',18:'S',19:'T',20:'U',21:'V',22:'W',23:'X',24:'Y',25:'Z',
            26:'a',27:'b',28:'c',29:'d',30:'e',31:'f',32:'g',33:'h',34:'i',35:'j',36:'k',37:'l',38:'m',39:'n',40:'o',41:'p',42:'q',43:'r',44:'s',45:'t',46:'u',47:'v',48:'w',49:'x',50:'y',51:'z',
            52:'0',53:'1',54:'2',55:'3',56:'4',57:'5',58:'6',59:'7',60:'8',61:'9',62:',',63:'.'}
int2code = lambda n: cvtTable[n//64] + cvtTable[n%64]

pad = lambda s: s + (16 - len(s) % 16) * chr(0)

str_to_hexStr = lambda string: binascii.hexlify(string.encode('utf-8')).decode('utf-8')

class net():
    def __init__(self,):

        # init wlan connect
        self.SSID="AS6666"
        self.password="ASDFghjkl"
        # init nb connect
        self.uart = UART(2,9600)
        self.uart.init(9600, bits=8, parity=None, stop=1)
        self.connect_instance = '0'


class NBnet():
    def __init__(self,):
        
    
    def get_signal(self,):
        self.uart.write('AT+CSQ\r')
        time.sleep(1)
        sig_s = self.uart.read()
        match = ure.search('CSQ:.*?,0',sig_s)
        sig_len = int(match.group(0)[5:-2])
        print('signal strentgh {}'.format(sig_len))
        return sig_len
    
    def build_connect(self,):
        self.uart.write('AT+CHTTPCREATE='+nbiot_upload_addr+'\r')
        time.sleep(3)
        con_res = self.uart.read()
        print(con_res)
        if ure.search('ERROR',con_res) == None:
            print('init succeed')
        else:
            return False
        
    def destory_connect(self,):
        self.uart.write('AT+CHTTPDESTORY='+self.connect_instance+'\r')
        time.sleep_ms(500)
        des_res = self.uart.read()
        print(des_res)
        
    def send_data(self, data):
        for i in range(4):
            #connect service(prepare send)
            self.uart.write('AT+CHTTPCON='+self.connect_instance+'\r')
            time.sleep(2)
            con_res = self.uart.read()
            print('try time : {}, connect code : {}'.format(i,con_res))
            if ure.search('OK',con_res) != None:
                break
            elif i == 5:
                print('Fail to connect!')
                return False
        time.sleep(1)
        # build send AT command
        # paramter : <client_id> <method> <path> <header> <type> <content>
        send_at_command = 'AT+CHTTPSEND='+ self.connect_instance +',1,"'+ nbiot_upload_path +'",'+ '"{1234}"' +',,"'+ data +'"\r'
        print(send_at_command)
        for j in range(3):
            #connect service(prepare send)
            self.uart.write(send_at_command)
            time.sleep(5)
            send_res = self.uart.read()
            print('try time : {}, connect code : {}'.format(j,send_res))
            if ure.search('OK',send_res) != None:
                break
        self.uart.write('AT+CHTTPDISCON='+self.connect_instance+'\r')
        time.sleep_ms(500)
        discon_res = self.uart.read()
        print(discon_res)
        return True  

heartline = ''

def check(_):
    global client
    client.check_msg()

def mqtt_callback(topic, msg):
    global return_format, return_path
    #print('topic: {}'.format(topic))
    msg = ujson.loads(msg.decode('utf-8'))['paras']
    screen.add_last(msg['status'], msg['bpm'])
    msg_id = topic.decode("utf-8").split('=',1)[1]      # get msg id
    #print(return_path+msg_id)
    client.publish(return_path+msg_id, msg=return_template, qos=0)

def connectWIFI():
    screen.net()
    blue.value(1)
    global SSID, password
    wlan=network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.disconnect()
    wlan.connect(SSID,password)
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

def send():
    global heartline
    screen.trans()
    ready_up = upload_format.copy()
    ready_up['services'][0]['properties']['data'] = heartline
    client.publish(upload_path, msg=ujson.dumps(ready_up), qos=0)
    del ready_up, heartline
    print('Successfully Sent')
    
def get_adc():
    global heartline
    heartline=''
    screen.record()
    tim.init(period=5, mode=Timer.PERIODIC, callback=rec)
    time.sleep_ms(16000)
    tim.deinit()
    
def rec(_):
    global heartline
    heartline += int2code(adc0.read())

class screen_show():
    def __init__(self):
        self.bpm = None
        display.fill(1)
        display.show()
        time.sleep_ms(500)
        display.fill(0)
        display.show()
    
    def record(self):
        display.fill(0)
        display.text('Status:',0,1)
        from icon import heart_icon
        for y, row in enumerate(heart_icon):
            for x, c in enumerate(row):
                display.pixel(x+58, y+1, c)
        del heart_icon
        display.text('Recording ECG',0,12)
        if self.bpm != None:
            self.last()
        display.show()

    def trans(self):
        display.fill(0)
        display.text('Status:',0,1)
        from icon import upload_icon
        for y, row in enumerate(upload_icon):
            for x, c in enumerate(row):
                display.pixel(x+58, y+1, c)
        display.vline(62,0,9,1)
        display.text('Uploading data',0,12)
        if self.bpm != None:
            self.last()
        del upload_icon
        display.show()
        
    def net(self):
        display.fill(0)
        from icon import wifi_icon
        for y, row in enumerate(wifi_icon):
            for x, c in enumerate(row):
                display.pixel(x+3, y+2, c)
        display.text('Connect to WiFi',0,14,1)
        display.text('SSID:'+SSID,0,24,1)
        if self.bpm != None:
            self.last()
        del wifi_icon
        display.show()
    
    def wait(self):
        display.fill(0)
        display.text('Status: ',0,1)
        display.text('Wait Analysis',0,12)
        if self.bpm != None:
            self.last()
        display.show()
        
    def last(self):
        display.vline(0,26,3,1)
        display.vline(8,26,3,1)
        display.hline(3,23,3,1)
        display.hline(3,31,3,1)
        display.fill_rect(1,24,7,7,1)
        display.text(str(self.bpm)+' BPM',13,24,1)
    
    def add_last(self,status,bpm):
        self.bpm = bpm
        self.status = status
time.sleep_ms(500)
# initialize finished
blue.value(0)
riner_pwm.deinit()
if __name__ == '__main__':
    screen = screen_show()
    connectWIFI()
    
    client = MQTTClient(client_id, url, port ,user=usr, password=pwd, keepalive=600)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(download_path)
    while True:
        get_adc()
        send()
        screen.wait()
        client.wait_msg()
        















'''''''''''''''

from machine import Pin, PWM, ADC, reset, RTC, Timer, I2C, UART
import ssd1306, network, time, ujson, ure, binascii
from urequest import urlopen

# define basic objects : screen, clock, led,adc
i2c = I2C(1,scl=Pin(23),sda=Pin(22))
display = ssd1306.SSD1306_I2C(128,32,i2c)
rtc = RTC
tim = Timer(-1)
blue = Pin(2,Pin.OUT)
riner_low = Pin(19,Pin.OUT)
riner_low.value(0)
riner_pwm = PWM(Pin(18), freq=550, duty=512)
riner_pwm.init()
adc0=ADC(Pin(32))
adc0.atten(ADC.ATTN_11DB)
adc0.width(ADC.WIDTH_12BIT)

class NetWork():
    def __init__(self,):
        # set target address
        self.address = "http://121.36.108.69P:881/test"
        
        # init wlan connect
        self.SSID = "AS6666"
        self.passwd = "ASDFghjkl"
        # init nb connect
        self.uart = UART(2,9600)
        self.uart.init(9600, bits=8, parity=None, stop=1)
        self.connect_instance = '0'
        self.net_status = 0
        
    def connect_WLAN(self,):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.disconnect()
        wlan.connect(self.SSID,self.passwd)
        ct = 0
        while(wlan.ifconfig()[0]=='0.0.0.0'):
            time.sleep_ms(500)
            ct += 1
            if ct==40: return False
        self.net_status = 2
        return True
    
    def send_via_WLAN(self, data):
        response = urlopen(self.address, data, "POST")
        print(response)
        return response
    

net = NetWork()
net.connect_WLAN()
net.send_via_WLAN(b'1234567')
