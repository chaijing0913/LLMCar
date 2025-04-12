#include "esp_camera.h"
#include <WiFi.h>
#include "AsyncUDP.h"
#include <vector>

const char *ssid = "chai";
const char *password = "chaijing0913";

#define maxcache 1430

//设置每次发送最大的数据量，如果选择一次发送会出现丢失数据，经测试，我这边每
//次最大发送1436，选择一个稍微小点的数
AsyncUDP udp;  //异步udp既可以发送也可以接收

#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

static camera_config_t camera_config = {
  .pin_pwdn = PWDN_GPIO_NUM,
  .pin_reset = RESET_GPIO_NUM,
  .pin_xclk = XCLK_GPIO_NUM,
  .pin_sscb_sda = SIOD_GPIO_NUM,
  .pin_sscb_scl = SIOC_GPIO_NUM,

  .pin_d7 = Y9_GPIO_NUM,
  .pin_d6 = Y8_GPIO_NUM,
  .pin_d5 = Y7_GPIO_NUM,
  .pin_d4 = Y6_GPIO_NUM,
  .pin_d3 = Y5_GPIO_NUM,
  .pin_d2 = Y4_GPIO_NUM,
  .pin_d1 = Y3_GPIO_NUM,
  .pin_d0 = Y2_GPIO_NUM,
  .pin_vsync = VSYNC_GPIO_NUM,
  .pin_href = HREF_GPIO_NUM,
  .pin_pclk = PCLK_GPIO_NUM,

  .xclk_freq_hz = 20000000,
  .ledc_timer = LEDC_TIMER_0,
  .ledc_channel = LEDC_CHANNEL_0,

  .pixel_format = PIXFORMAT_JPEG,
  // ESP32端修改
  .frame_size = FRAMESIZE_VGA,  //.frame_size = FRAMESIZE_QVGA,  // 320x240, .frame_size = FRAMESIZE_VGA,
  .jpeg_quality = 12,
  .fb_count = 1,
};

esp_err_t camera_init() {
  //initialize the camera
  esp_err_t err = esp_camera_init(&camera_config);
  if (err != ESP_OK) {
    Serial.println("Camera Init Failed!");
    return err;
  }
  sensor_t *s = esp_camera_sensor_get();
  //initial sensors are flipped vertically and colors are a bit saturated
  if (s->id.PID == OV2640_PID) {
    s->set_vflip(s, 1);  //flip it back
    //        s->set_brightness(s, 1);//up the blightness just a bit，亮度-2~2
    //        s->set_contrast(s, 1); //对比度-2~2
    //        s->set_saturation(s, -2);  // 饱和度（-2 到 2）
  }
  Serial.println("Camera Init OK!");
  return ESP_OK;
}

void wifi_init(void) {
  delay(10);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi Connected OK!");
  Serial.print("IP Address:");
  Serial.println(WiFi.localIP());
}


void setup() {
  Serial.begin(115200);
  camera_init();  //
  wifi_init();    //
  Serial.println("Sys Is Running!");
  //此部分可忽略
  if (udp.connect(IPAddress(172, 20, 10, 3), 8080)) {
    Serial.println("UDP Server Connected!");
    udp.onPacket([](AsyncUDPPacket packet) {
      Serial.print("UDP Packet Type: ");
      Serial.print(packet.isBroadcast() ? "Broadcast" : packet.isMulticast() ? "Multicast"
                                                                             : "Unicast");
      Serial.print(", From: ");
      Serial.print(packet.remoteIP());
      Serial.print(":");
      Serial.print(packet.remotePort());
      Serial.print(", To: ");
      Serial.print(packet.localIP());
      Serial.print(":");
      Serial.print(packet.localPort());
      Serial.print(", Length: ");
      Serial.print(packet.length());
      Serial.print(", Data: ");
      Serial.write(packet.data(), packet.length());
      Serial.println();
      //reply to the client
      packet.printf("Got %u bytes of data", packet.length());
    });
    //Send unicast
    //udp.print("Hello Server!");
  }
  //忽略到此部分
}

void loop() {
  if (udp.connect(IPAddress(172, 20, 10, 3), 8080))  //连接远端的udp
  {
    while (true) {
      //acquire a frame
      camera_fb_t *fb = esp_camera_fb_get();
      uint8_t *temp = fb->buf;  //这个是为了保存一个地址，在摄像头数据发送完毕后需要返回，否则会出现板子发送一段时间后自动重启，不断重复
      if (!fb) {
        Serial.print("Camera Capture Failed!");
      } else {
        // 将图片数据分段发送
        int leng = fb->len;
        int timess = leng / maxcache;
        int extra = leng % maxcache;
        for (int j = 0; j < timess; j++) {
          udp.write(fb->buf, maxcache);
          for (int i = 0; i < maxcache; i++) {
            fb->buf++;
          }
        }
        udp.write(fb->buf, extra);
        udp.println();
        udp.print("Frame Over");
        Serial.print("This Frame Length:");
        Serial.print(fb->len);
        Serial.println(".Succes To Send Image For UDP");
        //return the frame buffer back to the driver for reuse
        fb->buf = temp;            //将当时保存的指针重新返还
        esp_camera_fb_return(fb);  //这一步在发送完毕后要执行，具体作用还未可知。
      }
      //delay(60000);
      delay(20);  //不加延时会导致数据发送混乱 稍微延时增加数据传输可靠性
    }
  } else {
    Serial.println("Connected UDP Server Fail,After 10 Seconds Try Again!");
  }
  delay(10000);
}
