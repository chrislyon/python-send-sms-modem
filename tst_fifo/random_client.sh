:
FIFO=./fifo
MY_NUM=$1
NB=$( echo $RANDOM | cut -c2)
echo "Nb : " $NB

N=0

for (( c=1 ; c<=$NB ; c++ ))
do
    let N=N+1
    T=$( echo $RANDOM | cut -c1)
    echo "Sleeping $T"
    sleep $T
    echo "0601234567:TEST $MY_NUM=$N/$NB"
    echo "0601234567:TEST $MY_NUM=$N/$NB" >> ./fifo
done
echo "0601234567:TEST $MY_NUM FINISHED"
echo "0601234567:TEST $MY_NUM FINISHED" >> ./fifo
