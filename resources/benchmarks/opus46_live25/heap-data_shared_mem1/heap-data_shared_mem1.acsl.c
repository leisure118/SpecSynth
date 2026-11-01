#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#include <stdlib.h>
struct mem {
    int val;
};
struct list_node {
    int x;
    struct mem *mem;
    struct list_node *next;
};
int main() {
    struct mem *m = malloc(sizeof(*m));
    //@ admit \valid(m);
    m->val = 100;
    struct list_node *head = malloc(sizeof(*head));
    //@ admit \valid(head);
    //@ admit \separated(m, head);
    head->x = 1;
    head->mem = m;
    head->next = head;
    struct list_node *list = head;
    /*@
      loop invariant \valid(m);
      loop invariant m->val == 100;
      loop invariant \valid(head);
      loop invariant head->x == 1;
      loop invariant head->mem == m;
      loop invariant list == head;
      loop invariant \separated(m, head);
      loop invariant head->next == head ||
        (\valid(head->next) && head->next->next == head &&
         head->next->mem == m && head->next->x > 0 &&
         head->next->x < 10 && \separated(head->next, m) &&
         \separated(head->next, head));
    */
    while (unknown()) {
        int x = unknown();
        if (x > 0 && x < 10) {
            struct list_node *n = malloc(sizeof(*n));
            //@ admit \valid(n);
            //@ admit \separated(n, m);
            //@ admit \separated(n, head);
            n->x = x;
            n->mem = m;
            n->next = head;
            list->next = n;
        }
    }
    list = head;
    /*@
      loop invariant \valid(list);
      loop invariant \valid(m);
      loop invariant list->mem == m;
      loop invariant list->x > 0;
      loop invariant list->x < 10;
      loop invariant \separated(list, m);
      loop invariant \valid(list->next);
      loop invariant list->next->mem == m;
      loop invariant list->next->x > 0;
      loop invariant list->next->x < 10;
      loop invariant \separated(list->next, m);
      loop invariant list->next->next == list;
      loop invariant m->val > 90 && m->val < 110;
      loop assigns m->val, list;
    */
    while (list) {
        if (list->mem->val <= 100)
            list->mem->val += list->x;
        else
            list->mem->val -= list->x;
        list = list->next;
        //@ assert(m->val > 90 && m->val < 110);
    }
}
