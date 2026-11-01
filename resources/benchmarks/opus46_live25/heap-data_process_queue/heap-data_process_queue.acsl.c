#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#include <stdlib.h>
#define MAX_PROC 1000
struct process_node {
    int process_id;
    int time_to_wait;
    struct process_node *next;
};

/*@ axiomatic QueueInvariant {
  predicate all_wait_ge_one{L}(struct process_node *p);

  axiom all_wait_null{L}:
    all_wait_ge_one{L}(\null);

  axiom all_wait_cons{L}: \forall struct process_node *p;
    \valid(p) ==> p->time_to_wait >= 1 ==> all_wait_ge_one{L}(p->next)
    ==> all_wait_ge_one{L}(p);

  axiom all_wait_head{L}: \forall struct process_node *p;
    all_wait_ge_one{L}(p) ==> p != \null ==> p->time_to_wait >= 1;

  axiom all_wait_valid{L}: \forall struct process_node *p;
    all_wait_ge_one{L}(p) ==> p != \null ==> \valid(p);

  axiom all_wait_tail{L}: \forall struct process_node *p;
    all_wait_ge_one{L}(p) ==> p != \null ==> all_wait_ge_one{L}(p->next);

  logic integer list_len{L}(struct process_node *p);

  axiom list_len_null{L}: list_len{L}(\null) == 0;

  axiom list_len_cons{L}: \forall struct process_node *p;
    \valid(p) ==> list_len{L}(p) == 1 + list_len{L}(p->next);

  axiom list_len_nonneg{L}: \forall struct process_node *p;
    list_len{L}(p) >= 0;
}
*/

/*@ assigns \nothing; */
void run_process(int id) { (void)id; }

/*@
  requires \valid(q);
  requires \valid(n);
  requires n->time_to_wait >= 1;
  requires all_wait_ge_one(*q);
  assigns n->next, *q;
  ensures all_wait_ge_one(*q);
*/
void append_to_queue(struct process_node *n, struct process_node **q) {
    n->next = *q;
    *q = n;
    //@ assert \valid(n) && n->time_to_wait >= 1 && all_wait_ge_one(n->next);
}

/*@
  requires \valid(q);
  requires all_wait_ge_one(*q);
  ensures all_wait_ge_one(*q);
*/
struct process_node *choose_next(struct process_node **q) {
    struct process_node *node = *q;
    struct process_node *prev = NULL;
    struct process_node *result = NULL;
    /*@
      loop invariant all_wait_ge_one(node);
      loop invariant node == \null || \valid(node);
      loop invariant all_wait_ge_one(*q);
      loop assigns *q, node, prev, result;
      loop variant list_len(node);
    */
    while (node != NULL) {
        if (node->time_to_wait == 1) {
            result = node;
            if (prev == NULL)
                *q = node->next;
            else
                prev->next = node->next;
        } else {
            node->time_to_wait--;
        }
        prev = node;
        node = node->next;
    }
    //@ assert all_wait_ge_one(*q);
    return result;
}

/*@
  requires all_wait_ge_one(q);
  assigns \nothing;
*/
void check_queue(struct process_node *q) {
    /*@
      loop invariant all_wait_ge_one(n);
      loop assigns n;
      loop variant list_len(n);
    */
    for (struct process_node *n = q; n != NULL; n = n->next){
        //@ assert (n->time_to_wait >= 1);
    }
}

int main() {
    struct process_node *queue = NULL;
    int next_time = 1;
    /*@
      loop invariant all_wait_ge_one(queue);
      loop invariant next_time >= 1;
    */
    while (unknown()) {
        if (next_time < MAX_PROC && unknown()) {
            int new_id = unknown();
            struct process_node *new_process = malloc(sizeof(*new_process));
            //@ admit \valid(new_process);
            new_process->process_id = unknown();
            new_process->time_to_wait = next_time++;
            append_to_queue(new_process, &queue);
        } else if (next_time > 1){
            struct process_node *p = choose_next(&queue);
            next_time--;
            run_process(p->process_id);
        }
        check_queue(queue);
    }
}
