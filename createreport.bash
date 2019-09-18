#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
python $DIR/report.py
cp $DIR/report.svg /var/www/grav-admin/user/pages/images/.
