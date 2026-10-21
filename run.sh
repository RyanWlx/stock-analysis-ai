#!/bin/bash

# $Name : run.sh
# $Version : v3.0
# $Function : java--spring-boot
# $Author : changyk
# $Create-Date : 2022-01-05
# $Description : start| stop | help

source /etc/profile

PY_FILE='main.py'
RUN_SKY=""

RUN_OPTIONS=''
RUN_PARAMS=''

PID_FILE="run.pid"
LOG_FILE="run.log"

DUMP_FLAG=false

BASE_PATH=$(cd `dirname $0`; pwd)
cd $BASE_PATH


echo_red() {
    echo -e "\033[31m $1 \033[0m"
}

echo_blue() {
    echo -e "\033[34m $1 \033[0m"
}

echo_yellow() {
    echo -e "\033[33m $1 \033[0m"
}

usage() {
    echo_red "Usage: $0 [start|stop|status|restart]"
}

# 判断当前服务是否运行
exec_status(){
    ## ps -ef 查询 \ pidfile文件存在  and  两值相同
    # 进程存在 ps -ef \ pid 文件
    # 进程不存在 ps -ef \ pid 文件

    echo_blue "----执行 status 方法----"

    FLAG=`ps -ef | grep $BASE_PATH/$PY_FILE | grep -v grep | wc -l`

    if [[ ! -z ${FLAG} ]]; then
        PS_PID=`ps -ef | grep python | grep $BASE_PATH/$PY_FILE | grep -v grep | awk '{print $2}'`
    else
        PS_PID=0
    fi


    ## pid文件不存在
    if [ ! -e $PID_FILE ]; then
        if [[ ! -z ${PS_PID} ]];then
            echo_red "${PY_FILE} 程序在运行中。。。。。。
            但 pid文件 不存在，进程内对应 Pid is ${PS_PID}。
            请处理 ---- 需手动杀进程后，重启"
        else
            echo_red "${PY_FILE}  pid-file 不存在,程序未运行。"
        fi

        return 0

    ## pid文件存在
    else
        FILE_PID=`cat $PID_FILE`
        if [[ ! -z ${PS_PID} ]];then

            if [[ ${PS_PID} == ${FILE_PID} ]]; then
                echo_yellow "${PY_FILE} 存在，且程序运行中。。。。。。Pid is ${PS_PID}"
                return 1
            else
                echo_red "${PY_FILE} 存在，pid-文件内 is ${FILE_PID}.
                程序运行中--- 进程内对应 Pid is ${PS_PID} ####
                实际运行 PID 为 ${PS_PID}.
                pid文件 与 实际运行 pid 号不同。
                请处理--需手动杀进程后，重启"
                return 0
            fi

        else
            echo_yellow "${PY_FILE}  pid-file 存在, 但进程内未查询到对应进程。。。。。请重启"
            return 0
        fi

    fi
}
# 启动
exec_start(){
    echo_blue "----执行 start 方法----"

    exec_status

    if [ $? -eq "1" ]; then
        echo_yellow "${PY_FILE} running. "
        exit 1
    else
        nohup python3  ./main.py > ../logs/run.log 2>&1 &
    fi

    echo_blue "${PY_FILE} -----------启动------------"

    PID=$!
    echo $! > ./$PID_FILE

    echo_blue "
    ---- BASE_PATH:     $BASE_PATH
    ---- PY_FILE:      $PY_FILE
    ---- RUN_OPTIONS:   $RUN_OPTIONS
    ---- RUN_PARAMS:    $RUN_PARAMS
    ---- OPTION:        $FUNCNAME
    ---- PID:           $PID
    ---- PID_FILE:      $PID_FILE
    ---- LOG_FILE:      $LOG_FILE
    "

    sleep 10
    exec_status
}


# 停止
exec_stop(){
    echo_blue "----执行 stop 方法----"
    exec_status

    # [$? -eq "1"] 说明pid不等于空 说明服务正在运行中，将进程号杀死
    if [ $? -eq "1" ]; then
        FILE_PID=`cat $PID_FILE`

        kill -9 $FILE_PID
        rm -f $PID_FILE
        echo_blue "${PY_FILE},  pid ${FILE_PID} stopped"
    else
        echo_yellow "${PY_FILE} not running"
        if [ ! -d $PID_FILE ]; then
            rm -f  $PID_FILE
        fi
    fi

}

main(){
    case $1 in
        start)
            exec_start
            ;;
        stop)
            exec_stop
            ;;
        restart)
            exec_stop
            sleep 5
            exec_start
            ;;
        status)
            exec_status
            ;;
        *)
            usage
            exit 1
            ;;
    esac
    exit 0
}

main $1
