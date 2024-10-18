#!/bin/bash

for solver in soc.pi mks.pi
do

    for file in instances/*
    do
        name=$(echo $file | cut -d/ -f2)
        echo solving $name

        timeout 100 ./picat $solver $file > tmp

        cost=$(grep "Cost" tmp | cut -d" " -f2)
        el_time=$(grep CPU tmp | cut -d" " -f3)

        echo $name'\t'$solver'\t'$cost'\t'$el_time >> results.txt
        rm -f tmp

        echo "done"
    done
done