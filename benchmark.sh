#!/bin/sh

delay=1
args=("$@")
N_1_threads=1
# N_1_threads=$(grep processor /proc/cpuinfo | tail -n 1 | awk '{print $NF}')

re0='^[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3}$'
re1='^[0-9]+$'
re2='^[0-9]+$'
re3='^[0-9]*$'

print_invalid () {
    printf "Invalid input!\n" >& 2;
    printf "Usage: $0 address port N(the number of seconds to benchmark, N must not be less than 10) concurrency(number of processes of the client, default is number of threads - 1)\n" >& 2
}

setup () {
    if [[ ! ${args[0]} =~ $re0 || ! ${args[1]} =~ $re1 || ! ${args[3]} =~ $re3 ]]; then
        print_invalid
        exit 1
    fi

    address=${args[0]}
    port=${args[1]}
    [[ -z ${args[3]} ]] || N_1_threads=${args[3]}

    if [[ ! ${args[2]} =~ $re2 || ${args[2]} -lt 10 ]]; then
        print_invalid
        exit 2
    else
        period=${args[2]}
    fi
}

main () {
    (python3 server.py $address $port > /dev/null & sleep $(( $period + $delay )); kill "$(jobs -p)" ) &

    sleep $delay
    for i in $(seq 1 $N_1_threads); do
        python3 client.py $address $port > /dev/null 2>&1 &
    done

    sleep $period
    stty sane
}

setup
main
