import threading
import time

import cv2

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image

from cv_bridge import CvBridge

from flask import (
    Flask,
    render_template_string,
    request,
    jsonify,
    Response
)


# ============================================================
# Flask
# ============================================================

app = Flask(__name__)

ros_node = None


# ============================================================
# CAMERA CONFIGURATION
# ============================================================

# Topic ảnh màu của RealSense D435i
#
# Kiểm tra bằng:
#
# ros2 topic list | grep image
#
CAMERA_TOPIC = "/camera/camera/color/image_raw"


# Chất lượng JPEG
#
# 50 - nhẹ CPU / nhẹ WiFi
# 60 - khá tốt
# 70 - chất lượng cao hơn nhưng nặng hơn
#
JPEG_QUALITY = 60


# FPS tối đa gửi camera
#
# 10-15 FPS phù hợp Pi4
#
CAMERA_FPS = 15


# ============================================================
# WEB INTERFACE
# ============================================================

HTML = """
<!DOCTYPE html>

<html>

<head>

    <meta name="viewport"
          content="width=device-width,
                   initial-scale=1.0,
                   maximum-scale=1.0,
                   user-scalable=no">

    <title>EDDIE BOT</title>


    <style>

        * {
            box-sizing: border-box;
        }


        html,
        body {

            margin: 0;

            padding: 0;

            width: 100%;

            height: 100%;

            overflow: hidden;

            background: #111;

            color: white;

            font-family: Arial, sans-serif;

            touch-action: none;

            user-select: none;

            -webkit-user-select: none;

        }


        /* ====================================================
           MAIN
           ==================================================== */

        #main {

            width: 100vw;

            height: 100vh;

            display: flex;

            flex-direction: row;

        }


        /* ====================================================
           LEFT - JOYSTICK
           ==================================================== */

        #controller {

            width: 40%;

            height: 100%;

            display: flex;

            flex-direction: column;

            align-items: center;

            justify-content: center;

            padding: 10px;

        }


        #title {

            font-size: 25px;

            font-weight: bold;

            margin-bottom: 4px;

        }


        #status {

            font-size: 13px;

            color: #aaa;

            margin-bottom: 8px;

        }


        #values {

            display: flex;

            gap: 20px;

            margin-bottom: 10px;

        }


        .value {

            font-size: 16px;

        }


        /* ====================================================
           JOYSTICK
           ==================================================== */

        #joystick {

            width: 250px;

            height: 250px;

            background: #333;

            border-radius: 50%;

            position: relative;

            touch-action: none;

            box-shadow:
                inset 0 0 20px rgba(0, 0, 0, 0.6);

        }


        #stick {

            width: 80px;

            height: 80px;

            background: #777;

            border-radius: 50%;

            position: absolute;

            left: 85px;

            top: 85px;

            box-shadow:
                0 3px 10px rgba(0, 0, 0, 0.5);

        }


        /* ====================================================
           STOP
           ==================================================== */

        #stop {

            width: 180px;

            height: 55px;

            margin-top: 12px;

            background: red;

            color: white;

            border: none;

            border-radius: 12px;

            font-size: 24px;

            font-weight: bold;

        }


        #stop:active {

            background: darkred;

        }


        /* ====================================================
           RIGHT - CAMERA
           ==================================================== */

        #camera-container {

            width: 60%;

            height: 100%;

            padding: 10px;

            display: flex;

            align-items: center;

            justify-content: center;

        }


        #camera-box {

            width: 100%;

            height: 100%;

            background: #222;

            border: 2px solid #444;

            border-radius: 10px;

            overflow: hidden;

            position: relative;

            display: flex;

            align-items: center;

            justify-content: center;

        }


        #camera {

            width: 100%;

            height: 100%;

            object-fit: contain;

        }


        #camera-title {

            position: absolute;

            top: 10px;

            left: 10px;

            z-index: 10;

            background: rgba(0, 0, 0, 0.65);

            padding: 6px 10px;

            border-radius: 6px;

            font-size: 14px;

        }


        /* ====================================================
           ROTATE MESSAGE
           ==================================================== */

        #rotate-message {

            display: none;

            position: fixed;

            top: 0;

            left: 0;

            width: 100vw;

            height: 100vh;

            background: #111;

            color: white;

            z-index: 1000;

            align-items: center;

            justify-content: center;

            text-align: center;

            font-size: 24px;

            padding: 30px;

        }


        @media (orientation: portrait) {

            #rotate-message {

                display: flex;

            }

        }


    </style>

</head>


<body>


<!-- ========================================================
     ROTATE WARNING
     ======================================================== -->

<div id="rotate-message">

    Hãy xoay điện thoại sang ngang

    <br><br>

    ↻

</div>


<!-- ========================================================
     MAIN
     ======================================================== -->

<div id="main">


    <!-- ====================================================
         LEFT
         ==================================================== -->

    <div id="controller">


        <div id="title">

            EDDIE BOT

        </div>


        <div id="status">

            PHONE CONTROL

        </div>


        <div id="values">


            <div class="value">

                V:

                <span id="linear">

                    0.00

                </span>

                m/s

            </div>


            <div class="value">

                W:

                <span id="angular">

                    0.00

                </span>

                rad/s

            </div>


        </div>


        <div id="joystick">

            <div id="stick"></div>

        </div>


        <button id="stop">

            STOP

        </button>


    </div>


    <!-- ====================================================
         RIGHT
         ==================================================== -->

    <div id="camera-container">


        <div id="camera-box">


            <div id="camera-title">

                REALSENSE D435i

            </div>


            <img
                id="camera"
                src="/video_feed"
            >


        </div>


    </div>


</div>


<script>


// ============================================================
// JOYSTICK CONFIGURATION
// ============================================================


// Bán kính joystick

const maxDistance = 85;


// Tốc độ tối đa

const MAX_LINEAR = 0.30;


// Tốc độ quay tối đa

const MAX_ANGULAR = 1.00;


// Deadzone

const DEADZONE = 0.10;


// Gửi command 20 Hz

const COMMAND_INTERVAL = 50;


// ============================================================
// STATE
// ============================================================

let active = false;


let joystickLinear = 0.0;

let joystickAngular = 0.0;


// ============================================================
// DOM
// ============================================================

const joystick =
    document.getElementById(
        "joystick"
    );


const stick =
    document.getElementById(
        "stick"
    );


const linearText =
    document.getElementById(
        "linear"
    );


const angularText =
    document.getElementById(
        "angular"
    );


// ============================================================
// JOYSTICK FUNCTION
// ============================================================

function applyJoystick(value)
{

    let sign = 1;


    if (value < 0)
    {

        sign = -1;

    }


    let v =
        Math.abs(value);


    // Deadzone

    if (v < DEADZONE)
    {

        return 0;

    }


    // Loại bỏ deadzone

    v =
        (v - DEADZONE)
        /
        (1.0 - DEADZONE);


    // Phi tuyến
    //
    // Gần tâm:
    // rất chậm
    //
    // Kéo xa:
    // nhanh hơn

    v = v * v;


    return sign * v;

}


// ============================================================
// PROCESS JOYSTICK
// ============================================================

function processJoystick(
    clientX,
    clientY
)
{

    const rect =
        joystick.getBoundingClientRect();


    const centerX =
        rect.left +
        rect.width / 2;


    const centerY =
        rect.top +
        rect.height / 2;


    let x =
        clientX - centerX;


    let y =
        clientY - centerY;


    let distance =
        Math.sqrt(
            x * x +
            y * y
        );


    // Giới hạn

    if (distance > maxDistance)
    {

        x =
            x *
            maxDistance /
            distance;


        y =
            y *
            maxDistance /
            distance;

    }


    // Di chuyển cần

    stick.style.left =
        (x + 85) + "px";


    stick.style.top =
        (y + 85) + "px";


    // ========================================================
    // LINEAR
    // ========================================================

    let linear =
        applyJoystick(
            -y / maxDistance
        );


    // ========================================================
    // ANGULAR
    // ========================================================

    let angular =
        applyJoystick(
            -x / maxDistance
        );


    // Scale

    linear *= MAX_LINEAR;

    angular *= MAX_ANGULAR;


    // Target

    joystickLinear =
        linear;


    joystickAngular =
        angular;


    // Hiển thị

    linearText.innerText =
        linear.toFixed(2);


    angularText.innerText =
        angular.toFixed(2);

}


// ============================================================
// RESET JOYSTICK
// ============================================================

function resetJoystick()
{

    active = false;


    joystickLinear = 0.0;

    joystickAngular = 0.0;


    stick.style.left =
        "85px";


    stick.style.top =
        "85px";


    linearText.innerText =
        "0.00";


    angularText.innerText =
        "0.00";


    // Gửi STOP ngay

    sendCommand();

}


// ============================================================
// SEND COMMAND
// ============================================================

function sendCommand()
{

    fetch(
        "/cmd",
        {

            method: "POST",

            headers:
            {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify(
                {

                    linear:
                        joystickLinear,

                    angular:
                        joystickAngular

                })

        }
    )

    .catch(
        function(error)
        {

            console.log(
                "Connection error:",
                error
            );

        }
    );

}


// ============================================================
// 20 Hz
// ============================================================

setInterval(

    sendCommand,

    COMMAND_INTERVAL

);


// ============================================================
// TOUCH START
// ============================================================

joystick.addEventListener(

    "touchstart",

    function(e)
    {

        active = true;

        e.preventDefault();

    },

    {
        passive: false
    }

);


// ============================================================
// TOUCH MOVE
// ============================================================

joystick.addEventListener(

    "touchmove",

    function(e)
    {

        if (!active)
        {

            return;

        }


        e.preventDefault();


        const touch =
            e.touches[0];


        processJoystick(

            touch.clientX,

            touch.clientY

        );

    },

    {
        passive: false
    }

);


// ============================================================
// TOUCH END
// ============================================================

joystick.addEventListener(

    "touchend",

    function(e)
    {

        resetJoystick();

    }

);


// ============================================================
// TOUCH CANCEL
// ============================================================

joystick.addEventListener(

    "touchcancel",

    function(e)
    {

        resetJoystick();

    }

);


// ============================================================
// STOP
// ============================================================

document
    .getElementById("stop")
    .addEventListener(

        "click",

        function()
        {

            resetJoystick();

        }

    );


</script>


</body>

</html>
"""


# ============================================================
# ROS 2 NODE
# ============================================================

class TeleopNode(Node):


    def __init__(self):

        super().__init__(
            "phone_teleop"
        )


        # ====================================================
        # CMD_VEL
        # ====================================================
        #
        # LƯU Ý:
        #
        # Nếu bạn đã dùng twist_mux theo cấu trúc:
        #
        # Joy   -> /joy/cmd_vel
        # Phone -> /phone/cmd_vel
        # Mux   -> /diff_cont/cmd_vel_unstamped
        #
        # THÌ ĐỔI topic bên dưới thành:
        #
        # "/phone/cmd_vel"
        #
        # Hiện tại để đúng với cấu hình trước của bạn:
        #

        self.publisher = self.create_publisher(

            Twist,

            "/phone/cmd_vel",

            10

        )


        # ====================================================
        # CAMERA
        # ====================================================

        self.bridge = CvBridge()


        self.latest_frame = None


        self.last_frame_time = 0.0


        self.frame_lock = threading.Lock()


        # ====================================================
        # CAMERA SUBSCRIBER
        # ====================================================

        self.image_subscriber = self.create_subscription(

                Image,

                CAMERA_TOPIC,

                self.image_callback,

                10

            )


        # ====================================================
        # TARGET VELOCITY
        # ====================================================

        self.target_linear = 0.0


        self.target_angular = 0.0


        # ====================================================
        # CURRENT VELOCITY
        # ====================================================

        self.current_linear = 0.0


        self.current_angular = 0.0


        # ====================================================
        # SAFETY
        # ====================================================

        self.last_command_time = time.time()


        # ====================================================
        # CONTROL LOOP
        # ====================================================

        self.timer = self.create_timer(

                0.05,

                self.control_loop

            )


        # ====================================================
        # LOG
        # ====================================================

        self.get_logger().info(
            "===================================="
        )

        self.get_logger().info(
            "EDDIE BOT PHONE TELEOP"
        )

        self.get_logger().info(
            "===================================="
        )

        self.get_logger().info(
            "CMD topic:"
        )

        self.get_logger().info(
            "/diff_cont/cmd_vel_unstamped"
        )

        self.get_logger().info(
            "Camera topic:"
        )

        self.get_logger().info(
            CAMERA_TOPIC
        )

        self.get_logger().info(
            "Max linear: 0.30 m/s"
        )

        self.get_logger().info(
            "Max angular: 1.00 rad/s"
        )


    # ========================================================
    # CAMERA CALLBACK
    # ========================================================

    def image_callback(self, msg):

        try:

            # ======================================================
            # ROS Image -> OpenCV
            # ======================================================

            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding="passthrough"
            )

            # ======================================================
            # RealSense đang publish rgb8
            # OpenCV sử dụng BGR
            # ======================================================

            if msg.encoding == "rgb8":
                frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_RGB2BGR
                )

            # ======================================================
            # Resize
            # ======================================================

            frame = cv2.resize(
                frame,
                (640, 480),
                interpolation=cv2.INTER_AREA
            )

            # ======================================================
            # JPEG encode
            # ======================================================

            encode_params = [
                int(cv2.IMWRITE_JPEG_QUALITY),
                JPEG_QUALITY
            ]

            success, encoded = cv2.imencode(
                ".jpg",
                frame,
                encode_params
            )

            if not success:
                self.get_logger().error(
                    "JPEG encode failed"
                )
                return

            # ======================================================
            # Convert JPEG -> bytes
            # ======================================================

            jpeg_data = encoded.tobytes()

            # ======================================================
            # Kiểm tra JPEG header
            # JPEG bắt đầu bằng FF D8
            # ======================================================

            if not jpeg_data.startswith(b"\xff\xd8"):

                self.get_logger().error(
                    "Invalid JPEG header"
                )
                return

            # ======================================================
            # Kiểm tra JPEG end
            # JPEG kết thúc bằng FF D9
            # ======================================================

            if not jpeg_data.endswith(b"\xff\xd9"):

                self.get_logger().error(
                    "Invalid JPEG end"
                )
                return

            # ======================================================
            # Lưu frame mới nhất
            # ======================================================

            with self.frame_lock:

                self.latest_frame = jpeg_data
                self.last_frame_time = time.time()

        except Exception as e:

            self.get_logger().error(
                "Camera error: " + str(e)
            )


    # ========================================================
    # SET TARGET
    # ========================================================

    def set_target(
        self,
        linear,
        angular
    ):

        # ====================================================
        # Limit linear
        # ====================================================

        linear = max(

                -0.30,

                min(

                    0.30,

                    linear

                )

            )


        # ====================================================
        # Limit angular
        # ====================================================

        angular = max(

                -1.00,

                min(

                    1.00,

                    angular

                )

            )


        self.target_linear = linear


        self.target_angular = angular


        self.last_command_time = time.time()


    # ========================================================
    # RAMP
    # ========================================================

    def ramp(
        self,
        current,
        target,
        step
    ):

        difference = target - current


        if abs(difference) <= step:

            return target


        if difference > 0:

            return current + step


        return current - step


    # ========================================================
    # CONTROL LOOP
    # ========================================================

    def control_loop(self):

        # ====================================================
        # SAFETY
        #
        # Nếu điện thoại mất command
        # > 0.3 giây
        #
        # => STOP
        # ====================================================

        if (

            time.time()
            -
            self.last_command_time

            >

            0.3

        ):

            self.target_linear = 0.0


            self.target_angular = 0.0


        # ====================================================
        # LINEAR RAMP
        # ====================================================

        self.current_linear = self.ramp(

                self.current_linear,

                self.target_linear,

                0.02

            )


        # ====================================================
        # ANGULAR RAMP
        # ====================================================

        self.current_angular = self.ramp(

                self.current_angular,

                self.target_angular,

                0.06

            )


        # ====================================================
        # PUBLISH
        # ====================================================

        msg = Twist()


        msg.linear.x = self.current_linear


        msg.angular.z = self.current_angular


        self.publisher.publish(
            msg
        )


# ============================================================
# FLASK INDEX
# ============================================================

@app.route("/")
def index():

    return render_template_string(
        HTML
    )


# ============================================================
# CMD API
# ============================================================

@app.route(
    "/cmd",
    methods=["POST"]
)
def command():

    try:

        data = request.get_json(
                silent=True
            )


        if data is None:

            return jsonify(

                {
                    "ok": False,

                    "error":
                        "Invalid JSON"

                }

            ), 400


        linear = float(

                data.get(
                    "linear",
                    0.0
                )

            )


        angular = float(

                data.get(
                    "angular",
                    0.0
                )

            )


        ros_node.set_target(

            linear,

            angular

        )


        return jsonify(

            {
                "ok": True
            }

        )


    except Exception as e:

        return jsonify(

            {

                "ok": False,

                "error":
                    str(e)

            }

        ), 400


# ============================================================
# CAMERA MJPEG STREAM
# ============================================================

def generate_frames():

    while True:

        with ros_node.frame_lock:
            frame = ros_node.latest_frame

        if frame is None:
            time.sleep(0.05)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: "
            + str(len(frame)).encode()
            + b"\r\n"
            b"\r\n"
            + frame
            + b"\r\n"
        )

        time.sleep(0.01)
# ============================================================
# CAMERA ROUTE
# ============================================================

@app.route("/video_feed")
def video_feed():

    return Response(

        generate_frames(),

        mimetype=
            "multipart/x-mixed-replace; boundary=frame"

    )


# ============================================================
# FLASK THREAD
# ============================================================

def flask_thread():
    import logging

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    app.run(
        host="0.0.0.0",
        port=8080,
        threaded=True,
        debug=False
    )


# ============================================================
# MAIN
# ============================================================

def main():

    global ros_node


    # ========================================================
    # ROS INIT
    # ========================================================

    rclpy.init()


    # ========================================================
    # CREATE NODE
    # ========================================================

    ros_node = TeleopNode()


    # ========================================================
    # FLASK THREAD
    # ========================================================

    thread = threading.Thread(

            target=flask_thread,

            daemon=True

        )


    thread.start()


    # ========================================================
    # ROS SPIN
    # ========================================================

    try:

        rclpy.spin(
            ros_node
        )


    except KeyboardInterrupt:

        pass


    finally:

        # ====================================================
        # STOP
        # ====================================================

        ros_node.target_linear = 0.0


        ros_node.target_angular = 0.0


        ros_node.current_linear = 0.0


        ros_node.current_angular = 0.0


        msg = Twist()


        msg.linear.x = 0.0


        msg.angular.z = 0.0


        ros_node.publisher.publish(
            msg
        )


        # ====================================================
        # DESTROY
        # ====================================================

        ros_node.destroy_node()


        rclpy.shutdown()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()