from setuptools import find_packages, setup

package_name = 'phone_teleop'

setup(
    name=package_name,
    version='0.0.0',

    packages=find_packages(exclude=['test']),

    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
    ],

    install_requires=[
        'setuptools',
    ],

    zip_safe=True,

    maintainer='hoanganh',
    maintainer_email='hoanganh@todo.todo',

    description='Phone WiFi teleoperation for ROS 2',

    license='Apache-2.0',

    tests_require=['pytest'],

    entry_points={
        'console_scripts': [
            'teleop_server = phone_teleop.teleop_server:main',
        ],
    },
)