NB=${1:-20}
N=0
for (( c=1 ; c<=$NB ; c++ ))
do
    let N=N+1
    sh random_client.sh $N &
done
wait
echo "STOP" >> fifo
