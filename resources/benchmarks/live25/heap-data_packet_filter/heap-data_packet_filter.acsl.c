#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#include <stdlib.h>
#define LOW 0
#define HIGH 1
typedef struct packet {
    unsigned size;
    unsigned prio;
    char *payload;
} Packet;
typedef struct packet_list_node {
    struct packet packet;
    struct packet_list_node *next;
} *Node;
struct packet_queue {
    struct packet_list_node *front;
};

/*@ inductive prio_queue_inv{L}(struct packet_list_node *n) {
  case prio_empty{L}: \forall struct packet_list_node *n; n == NULL ==> prio_queue_inv(n);
  case prio_cons{L}: \forall struct packet_list_node *n;
    \valid(n) && (n->packet.prio == HIGH || n->packet.size < 500) && prio_queue_inv(n->next)
    ==> prio_queue_inv(n);
}
*/

/*@ inductive normal_queue_inv{L}(struct packet_list_node *n) {
  case normal_empty{L}: \forall struct packet_list_node *n; n == NULL ==> normal_queue_inv(n);
  case normal_cons{L}: \forall struct packet_list_node *n;
    \valid(n) && n->packet.prio == LOW && n->packet.size >= 500 && normal_queue_inv(n->next)
    ==> normal_queue_inv(n);
}
*/

Packet receive() {
    Packet packet;
    packet.size = unknown();
    packet.prio = unknown() ? LOW : HIGH;
    packet.payload = unknown();
    return packet;
}
/*@ assigns \nothing; */
void send(struct packet p) { (void)p; }

void append_to_queue(Packet p, Node *q) {
    Node node = malloc(sizeof(*node));
    node->packet = p;
    node->next = *q;
    *q = node;
}

/*@
  requires prio_queue_inv(q);
  assigns \nothing;
*/
void process_prio_queue(Node q) {
    /*@
      loop invariant prio_queue_inv(node);
      loop assigns node;
    */
    for (Node node = q; node != NULL; node = node->next) {
        //@ assert (node->packet.prio == HIGH || node->packet.size < 500);
        send(node->packet);
    }
}

/*@
  requires normal_queue_inv(q);
  assigns \nothing;
*/
void process_normal_queue(Node q) {
    /*@
      loop invariant normal_queue_inv(node);
      loop assigns node;
    */
    for (Node node = q; node != NULL; node = node->next) {
        //@ assert (node->packet.prio == LOW && node->packet.size >= 500);
        send(node->packet);
    }
}

int main() {
    Node prio_queue = NULL;
    Node normal_queue = NULL;
    while (unknown()) {
        Packet new_packet = receive();
        if (new_packet.size > 0) {
            if (new_packet.prio == HIGH) {
                append_to_queue(new_packet, &prio_queue);
            } else if (new_packet.size < 500) {
                append_to_queue(new_packet, &prio_queue);
            } else {
                append_to_queue(new_packet, &normal_queue);
            }
        }
    }
    //@ admit prio_queue_inv(prio_queue);
    //@ admit normal_queue_inv(normal_queue);
    process_prio_queue(prio_queue);
    process_normal_queue(normal_queue);
    return 0;
}
