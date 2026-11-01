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

/*@ inductive all_prio(Node q) {
      case all_prio_nil: all_prio(\null);
      case all_prio_cons: \forall Node q;
        q != \null ==> \valid(q) ==>
        (q->packet.prio == HIGH || q->packet.size < 500) ==>
        all_prio(q->next) ==> all_prio(q);
    }
*/

/*@ inductive all_normal(Node q) {
      case all_normal_nil: all_normal(\null);
      case all_normal_cons: \forall Node q;
        q != \null ==> \valid(q) ==>
        (q->packet.prio == LOW && q->packet.size >= 500) ==>
        all_normal(q->next) ==> all_normal(q);
    }
*/

/*@
  assigns \nothing;
  ensures \result.prio == LOW || \result.prio == HIGH;
*/
Packet receive() {
    Packet packet;
    packet.size = unknown();
    packet.prio = unknown() ? LOW : HIGH;
    packet.payload = unknown();
    return packet;
}

/*@
  assigns \nothing;
*/
void send(struct packet p) { (void)p; }

/*@
  requires \valid(q);
  assigns *q;
  ensures all_prio(\old(*q)) && (\old(p).prio == HIGH || \old(p).size < 500) ==> all_prio(*q);
  ensures all_normal(\old(*q)) && (\old(p).prio == LOW && \old(p).size >= 500) ==> all_normal(*q);
*/
void append_to_queue(Packet p, Node *q);

/*@
  requires all_prio(q);
  assigns \nothing;
*/
void process_prio_queue(Node q) {
    /*@ loop invariant all_prio(node);
        loop assigns node;
    */
    for (Node node = q; node != NULL; node = node->next) {
        //@ assert (node->packet.prio == HIGH || node->packet.size < 500);
        send(node->packet);
    }
}

/*@
  requires all_normal(q);
  assigns \nothing;
*/
void process_normal_queue(Node q) {
    /*@ loop invariant all_normal(node);
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
    /*@ loop invariant all_prio(prio_queue);
        loop invariant all_normal(normal_queue);
        loop assigns prio_queue, normal_queue;
    */
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
    process_prio_queue(prio_queue);
    process_normal_queue(normal_queue);
    return 0;
}
