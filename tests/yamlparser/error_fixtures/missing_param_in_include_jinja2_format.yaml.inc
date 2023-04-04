- shell:
    command: !j2: |
      #!/bin/bash

      echo "hello, {{ unknown_one }}!"
