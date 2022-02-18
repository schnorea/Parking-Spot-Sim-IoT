# stop script on error
set -e

# Check to see if root CA file exists, download if not
if [ ! -f ./root-CA.crt ]; then
  printf "\nDownloading AWS IoT Root CA certificate from AWS...\n"
  curl https://www.amazontrust.com/repository/AmazonRootCA1.pem > root-CA.crt
fi

# Check to see if AWS Device SDK for Python exists, download if not
if [ ! -d ./aws-iot-device-sdk-python-v2 ]; then
  printf "\nCloning the AWS SDK...\n"
  git clone https://github.com/aws/aws-iot-device-sdk-python-v2.git
fi

# Check to see if AWS Device SDK for Python is already installed, install if not
if ! python -c "import awsiot" &> /dev/null; then
  printf "\nInstalling AWS SDK...\n"
  pushd aws-iot-device-sdk-python-v2
  python setup.py install
  result=$?
  popd
  if [ $result -ne 0 ]; then
    printf "\nERROR: Failed to install SDK.\n"
    exit $result
  fi
fi

# run pub/sub sample app using certificates downloaded in package
printf "\nRunning pub/sub sample application...\n"
python parkingspot.py --endpoint a3kf0d3b3a0ocb-ats.iot.us-east-1.amazonaws.com --root-ca AmazonRootCA1.cer --cert Parking2-certificate.pem.crt --key Parking2-private.pem.key --client-id basicPubSub --topic '$aws/rules/ParkingSpotEvent' --hours 0.1

#$aws/rules/ParkingSpotEvent