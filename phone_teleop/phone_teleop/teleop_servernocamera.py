import threading
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from flask import Flask, render_template_string, request, jsonify


# ============================================================
# Flask
# ============================================================

app = Flask(__name__)

ros_node = None


# ============================================================
# Camera
# ============================================================

# Thay địa chỉ này bằng địa chỉ stream camera của bạn.
#
# Ví dụ:
# CAMERA_URL = "http://192.168.5.178:8081/stream"
#
# Nếu chưa có camera stream:
# CAMERA_URL = ""
#
CAMERA_URL = ""


# ============================================================
# Web interface
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
           Main layout
           ==================================================== */

        #main {

            width: 100vw;

            height: 100vh;

            display: flex;

            flex-direction: row;

        }


        /* ====================================================
           Left side - controller
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

            font-size: 24px;

            font-weight: bold;

            margin-bottom: 5px;

        }


        #status {

            font-size: 14px;

            margin-bottom: 5px;

        }


        #values {

            width: 100%;

            display: flex;

            justify-content: center;

            gap: 20px;

            margin-bottom: 8px;

        }


        .value {

            font-size: 16px;

        }


        /* ====================================================
           Joystick
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
           Right side - camera
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

            display: flex;

            align-items: center;

            justify-content: center;

            position: relative;

        }


        #camera {

            width: 100%;

            height: 100%;

            object-fit: contain;

            display: none;

        }


        #camera-placeholder {

            text-align: center;

            color: #888;

            font-size: 20px;

        }


        #camera-title {

            position: absolute;

            top: 10px;

            left: 10px;

            z-index: 10;

            background: rgba(0, 0, 0, 0.6);

            padding: 6px 10px;

            border-radius: 6px;

            font-size: 15px;

        }


        /* ====================================================
           Portrait warning
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


        /* ====================================================
           Mobile portrait
           ==================================================== */

        @media (orientation: portrait) {

            #rotate-message {

                display: flex;

            }

        }


    </style>

</head>


<body>


<!-- ========================================================
     Rotate warning
     ======================================================== -->

<div id="rotate-message">

    Hãy xoay điện thoại sang ngang

    <br><br>

    ↻

</div>


<!-- ========================================================
     Main
     ======================================================== -->

<div id="main">


    <!-- ====================================================
         LEFT - JOYSTICK
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
         RIGHT - CAMERA
         ==================================================== -->

    <div id="camera-container">


        <div id="camera-box">


            <div id="camera-title">

                CAMERA

            </div>


            <div id="camera-placeholder">

                Camera chưa kết nối

            </div>


            <img
                id="camera"
                src="{{ camera_url }}"
            >


        </div>


    </div>


</div>


<script>


// ============================================================
// Configuration
// ============================================================


// Khoảng joystick

const maxDistance = 85;


// Tốc độ tối đa
//
// Tăng từ:
// 0.20 → 0.30 m/s

const MAX_LINEAR = 0.30;


// Góc quay tối đa

const MAX_ANGULAR = 1.00;


// Deadzone

const DEADZONE = 0.10;


// Tần số gửi command
//
// 20 Hz

const COMMAND_INTERVAL = 50;


// ============================================================
// State
// ============================================================

let active = false;


// Giá trị mục tiêu

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


const camera =
    document.getElementById(
        "camera"
    );


const cameraPlaceholder =
    document.getElementById(
        "camera-placeholder"
    );


// ============================================================
// Camera status
// ============================================================

if ("{{ camera_url }}" !== "")
{

    camera.style.display = "block";

    cameraPlaceholder.style.display =
        "none";

}


// ============================================================
// Apply joystick
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


    // Remove deadzone

    v =
        (v - DEADZONE)
        /
        (1.0 - DEADZONE);


    // Non-linear control
    //
    // Gần tâm → chậm
    // Kéo xa → nhanh

    v = v * v;


    return sign * v;

}


// ============================================================
// Process joystick
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


    // Hiển thị cần joystick

    stick.style.left =
        (x + 85) + "px";


    stick.style.top =
        (y + 85) + "px";


    // ========================================================
    // Linear
    // ========================================================

    let linear =
        applyJoystick(
            -y / maxDistance
        );


    // ========================================================
    // Angular
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
// Reset joystick
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
// Send command
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
// Fixed 20 Hz
// ============================================================

setInterval(
    sendCommand,
    COMMAND_INTERVAL
);


// ============================================================
// Touch start
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
// Touch move
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
// Touch end
// ============================================================

joystick.addEventListener(

    "touchend",

    function(e)
    {

        resetJoystick();

    }

);


// ============================================================
// Touch cancel
// ============================================================

joystick.addEventListener(

    "touchcancel",

    function(e)
    {

        resetJoystick();

    }

);


// ============================================================
// STOP button
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
# ROS 2 Node
# ============================================================

class TeleopNode(Node):


    def __init__(self):

        super().__init__(
            "phone_teleop"
        )


        # ====================================================
        # ROS topic
        # ====================================================

        self.publisher = self.create_publisher(

            Twist,

            "/diff_cont/cmd_vel_unstamped",

            10

        )


        # ====================================================
        # Target command
        # ====================================================

        self.target_linear = 0.0

        self.target_angular = 0.0


        # ====================================================
        # Current command
        # ====================================================

        self.current_linear = 0.0

        self.current_angular = 0.0


        # ====================================================
        # Control loop 20 Hz
        # ====================================================

        self.timer = self.create_timer(

            0.05,

            self.control_loop

        )


        # ====================================================
        # Safety
        # ====================================================

        self.last_command_time = time.time()


        self.get_logger().info(
            "===================================="
        )

        self.get_logger().info(
            "EDDIE BOT PHONE TELEOP"
        )

        self.get_logger().info(
            "Topic: "
            "/diff_cont/cmd_vel_unstamped"
        )

        self.get_logger().info(
            "Max linear: 0.30 m/s"
        )

        self.get_logger().info(
            "Max angular: 1.00 rad/s"
        )

        self.get_logger().info(
            "===================================="
        )


    # ========================================================
    # Set target
    # ========================================================

    def set_target(
        self,
        linear,
        angular
    ):

        # Giới hạn an toàn

        linear = max(
            -0.30,
            min(
                0.30,
                linear
            )
        )


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
    # Ramp
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
    # Control loop
    # ========================================================

    def control_loop(self):

        # ====================================================
        # Safety timeout
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
        # Linear ramp
        # ====================================================

        self.current_linear = self.ramp(

                self.current_linear,

                self.target_linear,

                0.02

            )


        # ====================================================
        # Angular ramp
        # ====================================================

        self.current_angular = self.ramp(

                self.current_angular,

                self.target_angular,

                0.06

            )


        # ====================================================
        # Publish
        # ====================================================

        msg = Twist()


        msg.linear.x = self.current_linear


        msg.angular.z = self.current_angular


        self.publisher.publish(
            msg
        )


# ============================================================
# Flask
# ============================================================

@app.route("/")
def index():

    return render_template_string(

        HTML,

        camera_url=CAMERA_URL

    )


# ============================================================
# Command API
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
                "error": str(e)
            }
        ), 400


# ============================================================
# Flask thread
# ============================================================

def flask_thread():

    app.run(

        host="0.0.0.0",

        port=8080,

        threaded=True,

        debug=False

    )


# ============================================================
# Main
# ============================================================

def main():

    global ros_node


    rclpy.init()


    ros_node = TeleopNode()


    thread = threading.Thread(

            target=flask_thread,

            daemon=True

        )


    thread.start()


    try:

        rclpy.spin(
            ros_node
        )


    except KeyboardInterrupt:

        pass


    finally:

        # STOP

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


        ros_node.destroy_node()


        rclpy.shutdown()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    main()