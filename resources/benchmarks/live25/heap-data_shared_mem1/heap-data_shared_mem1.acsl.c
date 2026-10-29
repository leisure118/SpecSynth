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
    m->val = 100;
    struct list_node *head = malloc(sizeof(*head));
    head->x = 1;
    head->mem = m;
    head->next = head;
    //@ admit \valid(m);
    //@ admit \valid(head);
    struct list_node *list = head;
    /*@
      loop invariant \valid(m);
      loop invariant \valid(head);
    */
    while (unknown()) {
        int x = unknown();
        if (x > 0 && x < 10) {
            struct list_node *n = malloc(sizeof(*n));
            n->x = x;
            n->mem = m;
            n->next = head;
            list->next = n;
        }
    }
    //@ admit head->mem == m;
    //@ admit head->x == 1;
    //@ admit m->val == 100;
    list = head;
    //@ admit \valid(head->next);
    //@ admit head->next->mem == m;
    //@ admit 1 <= head->next->x <= 9;
    //@ admit head->next->next == head;
    /*@
      loop invariant \valid(m);
      loop invariant \valid(list);
      loop invariant list == head || list == head->next;
      loop invariant list->mem == m;
      loop invariant 1 <= list->x <= 9;
      loop invariant 90 < m->val < 110;
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
