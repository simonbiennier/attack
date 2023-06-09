Flip your machine into forwarding mode (as root):
`echo "1" > /proc/sys/net/ipv4/ip_forward`

`iptables -I FORWARD -j NFQUEUE --queue-num 0`
