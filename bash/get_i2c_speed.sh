    #!/bin/bash
    BUS=1 # Change to your I2C bus number if different
    DTPATH=$(cat /proc/device-tree/aliases/i2c$BUS | tr -d '\0')
    od -An -td4 --endian=big /proc/device-tree$DTPATH/clock-frequency