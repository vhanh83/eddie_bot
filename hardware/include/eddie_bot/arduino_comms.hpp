#ifndef EDDIE_BOT__ARDUINO_COMMS_HPP
#define EDDIE_BOT__ARDUINO_COMMS_HPP

#include <sstream>
#include <cstdlib>
#include <cstdint>
#include <string>
#include <iostream>
#include <thread>
#include <atomic>
#include <mutex>

#include <libserial/SerialPort.h>


// ============================================================
// BAUD RATE
// ============================================================

LibSerial::BaudRate convert_baud_rate(int baud_rate)
{
  switch (baud_rate)
  {
    case 1200:   return LibSerial::BaudRate::BAUD_1200;
    case 1800:   return LibSerial::BaudRate::BAUD_1800;
    case 2400:   return LibSerial::BaudRate::BAUD_2400;
    case 4800:   return LibSerial::BaudRate::BAUD_4800;
    case 9600:   return LibSerial::BaudRate::BAUD_9600;
    case 19200:  return LibSerial::BaudRate::BAUD_19200;
    case 38400:  return LibSerial::BaudRate::BAUD_38400;
    case 57600:  return LibSerial::BaudRate::BAUD_57600;
    case 115200: return LibSerial::BaudRate::BAUD_115200;
    case 230400: return LibSerial::BaudRate::BAUD_230400;

    default:
      std::cout
        << "Error! Baud rate "
        << baud_rate
        << " not supported! Default to 57600"
        << std::endl;

      return LibSerial::BaudRate::BAUD_57600;
  }
}


// ============================================================
// ARDUINO COMMS
// ============================================================

class ArduinoComms
{
public:

  ArduinoComms()
    : timeout_ms_(100),
      encoder_1_(0),
      encoder_2_(0),
      last_motor_1_(0),
      last_motor_2_(0),
      rx_running_(false)
  {
  }


  ~ArduinoComms()
  {
    stop_receiver();

    if (serial_conn_.IsOpen())
    {
      serial_conn_.Close();
    }
  }


  // ==========================================================
  // CONNECT
  // ==========================================================

  void connect(
    const std::string &serial_device,
    int32_t baud_rate,
    int32_t timeout_ms)
  {
    timeout_ms_ = timeout_ms;

    serial_conn_.Open(serial_device);

    serial_conn_.SetBaudRate(
      convert_baud_rate(baud_rate));

    std::cout
      << "Serial connected: "
      << serial_device
      << " @ "
      << baud_rate
      << std::endl;

    // Bắt đầu thread nhận UART
    start_receiver();
  }


  // ==========================================================
  // DISCONNECT
  // ==========================================================

  void disconnect()
  {
    stop_receiver();

    if (serial_conn_.IsOpen())
    {
      serial_conn_.Close();

      std::cout
        << "Serial disconnected"
        << std::endl;
    }
  }


  // ==========================================================
  // CONNECTED
  // ==========================================================

  bool connected() const
  {
    return serial_conn_.IsOpen();
  }


  // ==========================================================
  // SEND COMMAND
  //
  // Chỉ gửi.
  // Không chờ response.
  // ==========================================================

  bool send_command(const std::string &msg)
{
  if (!serial_conn_.IsOpen())
  {
    std::cerr << "Serial port is not open" << std::endl;
    return false;
  }

  try
  {
    std::lock_guard<std::mutex> lock(tx_mutex_);

    serial_conn_.Write(msg);

    // Đảm bảo dữ liệu đã được đẩy ra UART
    serial_conn_.DrainWriteBuffer();

    //std::cout
     //<< "TX: "
     // << msg
      //<< std::endl;

    return true;
  }
  catch (const std::exception &e)
  {
    std::cerr
      << "Serial write error: "
      << e.what()
      << std::endl;

    return false;
  }
}

  // ==========================================================
  // START RECEIVER
  // ==========================================================

  void start_receiver()
  {
    if (rx_running_)
      return;

    rx_running_ = true;

    rx_thread_ =
      std::thread(
        &ArduinoComms::receiver_loop,
        this);

   // std::cout
     // << "UART RX thread started"
      //<< std::endl;
  }


  // ==========================================================
  // STOP RECEIVER
  // ==========================================================

  void stop_receiver()
  {
    if (!rx_running_)
      return;

    rx_running_ = false;

    if (rx_thread_.joinable())
    {
      rx_thread_.join();
    }

    std::cout
      << "UART RX thread stopped"
      << std::endl;
  }


  // ==========================================================
  // RECEIVER THREAD
  //
  // Đây chính là phần "event".
  //
  // Thread luôn kiểm tra UART.
  // Không cần read() của ros2_control gọi.
  // ==========================================================

  void receiver_loop()
{
    std::string frame;

    //std::cout << "RX thread running..." << std::endl;

    while (rx_running_)
    {
        try
        {
            if (!serial_conn_.IsOpen())
            {
                std::this_thread::sleep_for(
                    std::chrono::milliseconds(1));
                continue;
            }

            unsigned char byte = 0;

            // Chờ tối đa 1 ms để nhận 1 byte
            serial_conn_.ReadByte(byte, 1);

            // Debug byte nhận được
            //std::cout << "RX FRAME: " << frame << std::endl;


            // ==================================================
            // Bắt đầu một frame mới
            // ==================================================

            if (byte == '$')
            {
                frame.clear();
                frame += '$';
                continue;
            }


            // ==================================================
            // Đang nhận frame
            // ==================================================

            if (!frame.empty())
            {
                frame += static_cast<char>(byte);


                // ==================================================
                // '#' là ký tự kết thúc frame
                // ==================================================

                if (byte == '#')
                {
                    //std::cout
                        //<< "RX FRAME: "
                        //<< frame
                        //<< std::endl;


                    // Xử lý frame
                    process_frame(frame);


                    // Chuẩn bị nhận frame tiếp theo
                    frame.clear();
                }
            }
        }
        catch (const LibSerial::ReadTimeout&)
        {
            // Không có byte trong 1 ms.
            // Đây không phải lỗi.
            continue;
        }
        catch (const std::exception &e)
        {
           // std::cerr
               // << "RX ERROR: "
                //<< e.what()
                //<< std::endl;

            std::this_thread::sleep_for(
                std::chrono::milliseconds(1));
        }
    }

  //  std::cout
       // << "RX thread stopped"
       //<< std::endl;
}


  // ==========================================================
  // PARSE FRAME
  //
  // $1;GE;0;123456#
  //
  // address = 1
  // command = GE
  // option  = 0
  // value   = 123456
  // ==========================================================

  bool parse_frame(
    const std::string &frame,
    int &address,
    std::string &command,
    int &option,
    int64_t &value)
  {
    if (frame.empty())
      return false;


    std::string data = frame;


    // Kiểm tra '$'
    if (data.front() != '$')
      return false;


    // Bỏ '$'
    data.erase(0, 1);


    // Kiểm tra '#'
    if (data.empty() || data.back() != '#')
      return false;


    // Bỏ '#'
    data.pop_back();


    std::stringstream ss(data);

    std::string token_address;
    std::string token_command;
    std::string token_option;
    std::string token_value;


    if (!std::getline(
          ss,
          token_address,
          ';'))
      return false;


    if (!std::getline(
          ss,
          token_command,
          ';'))
      return false;


    if (!std::getline(
          ss,
          token_option,
          ';'))
      return false;


    if (!std::getline(
          ss,
          token_value,
          ';'))
      return false;


    try
    {
      address = std::stoi(token_address);

      command = token_command;

      option = std::stoi(token_option);

      value = std::stoll(token_value);
    }
    catch (...)
    {
      return false;
    }


    return true;
  }


  // ==========================================================
  // PROCESS FRAME
  //
  // Mọi frame từ STM32 đều đi qua đây.
  // ==========================================================

  void process_frame(
    const std::string &frame)
  {
    int address = 0;

    std::string command;

    int option = 0;

    int64_t value = 0;


    if (!parse_frame(
          frame,
          address,
          command,
          option,
          value))
    {
      std::cerr
        << "Invalid frame: "
        << frame
        << std::endl;

      return;
    }


    // ========================================================
    // DEBUG
    // ========================================================

   // std::cout
     // << "RX FRAME:"
     // << " Address=" << address
     // << " Command=" << command
     // << " Option=" << option
    //  << " Value=" << value
    //  << std::endl;


    // ========================================================
    // GE - ENCODER
    // ========================================================

    if (command == "GE")
    {
      std::lock_guard<std::mutex> lock(data_mutex_);


      if (address == 1)
      {
        encoder_1_ = value;

        // std::cout
        //   << "EVENT GE -> Encoder 1 = "
        //   << encoder_1_
        //   << std::endl;
      }
      else if (address == 2)
      {
        encoder_2_ = value;

        // std::cout
        //   << "EVENT GE -> Encoder 2 = "
        //   << encoder_2_
        //   << std::endl;
      }
    }


    // ========================================================
    // RE
    // ========================================================

    else if (command == "RE")
    {
      // std::cout
      //   << "EVENT RE:"
      //   << " Address=" << address
      //   << " Option=" << option
      //   << " Value=" << value
      //   << std::endl;
    }


    // ========================================================
    // SA
    // ========================================================

    else if (command == "SA")
    {
      // std::cout
      //   << "EVENT SA:"
      //   << " Address=" << address
      //   << " Option=" << option
      //   << " Value=" << value
      //   << std::endl;
    }


    // ========================================================
    // EN
    // ========================================================

    else if (command == "EN")
    {
      // std::cout
      //   << "EVENT EN:"
      //   << " Address=" << address
      //   << " Option=" << option
      //   << " Value=" << value
      //   << std::endl;
    }


    // ========================================================
    // COMMAND KHÁC
    // ========================================================

    else
    {
      // std::cout
      //   << "EVENT UNKNOWN:"
      //   << " Address=" << address
      //   << " Command=" << command
      //   << " Option=" << option
      //   << " Value=" << value
      //   << std::endl;
    }
  }


  // ==========================================================
  // READ ENCODER
  //
  // Không gửi GE.
  // Không chờ UART.
  //
  // Chỉ lấy giá trị mới nhất mà event đã nhận.
  // ==========================================================

  void read_encoder_values(
    int &val_1,
    int &val_2)
  {
    std::lock_guard<std::mutex> lock(data_mutex_);

    val_1 =
      static_cast<int>(encoder_1_);

    val_2 =
      static_cast<int>(encoder_2_);
  }


  // ==========================================================
  // REQUEST ENCODER
  //
  // Chỉ gửi request.
  // Receiver thread sẽ tự nhận response.
  // ==========================================================

  void request_encoder_values()
  {
    send_command("$1;GE;0;0#");

    send_command("$2;GE;0;0#");
  }


  // ==========================================================
  // SET MOTOR VALUES
  //
  // Không chờ response.
  // ==========================================================

  void set_motor_values(
  int val_1,
  int val_2)
{
  std::stringstream ss;

  // ========================================================
  // MOTOR 1
  // Chỉ gửi khi giá trị thay đổi
  // ========================================================

  if (val_1 != last_motor_1_)
  {
    ss << "$1;SS;2;" << val_1 << "#";

    if (send_command(ss.str()))
    {
      last_motor_1_ = val_1;
      // std::cout << "M1: " << val_1 << std::endl;
    }
  }


  // ========================================================
  // MOTOR 2
  // Chỉ gửi khi giá trị thay đổi
  // ========================================================

  if (val_2 != last_motor_2_)
  {
    ss.str("");
    ss.clear();

    ss << "$2;SS;2;" << val_2 << "#";

    if (send_command(ss.str()))
    {
      last_motor_2_ = val_2;
      // std::cout << "M2: " << val_2 << std::endl;
    }
  }
}


  // ==========================================================
  // GET ENCODER
  // ==========================================================

  int64_t get_encoder_1()
{
    std::lock_guard<std::mutex> lock(data_mutex_);
    return encoder_1_;
}

int64_t get_encoder_2()
{
    std::lock_guard<std::mutex> lock(data_mutex_);
    return encoder_2_;
}


private:

  LibSerial::SerialPort serial_conn_;


  int timeout_ms_;


  // ==========================================================
  // ENCODER DATA
  // ==========================================================

  int64_t encoder_1_;

  int64_t encoder_2_;
  int last_motor_1_ = 0;
  int last_motor_2_ = 0;


  // ==========================================================
  // RX THREAD
  // ==========================================================

  std::atomic<bool> rx_running_;

  std::thread rx_thread_;


  // ==========================================================
  // MUTEX
  // ==========================================================

  std::mutex data_mutex_;

  std::mutex tx_mutex_;
};


#endif // DIFFDRIVE_ARDUINO_ARDUINO_COMMS_HPP