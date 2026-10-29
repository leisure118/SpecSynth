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
    m->val = 0;
    struct list_node *head = malloc(sizeof(*head));
    head->x = 1;
    head->mem = m;
    head->next = head;
    //@ admit \valid(m);
    //@ admit \valid(head);
    //@ admit \separated(m, head);
    struct list_node *list = head;
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
    list = head;
    //@ admit \valid(list);
    //@ admit list->mem == m;
    //@ admit 0 <= m->val <= 100;
    /*@
      loop invariant \valid(list);
      loop invariant list->mem == m;
      loop invariant 0 <= m->val <= 100;
      loop assigns m->val, list;
    */
    while (m->val < 100) {
        //@ admit list->mem == m;
        if (list->mem->val + list->x <= 100)
            list->mem->val += list->x;
        //@ admit 0 <= m->val <= 100;
        //@ admit \valid(list->next) && list->next->mem == m;
        list = list->next;
    }
    //@ assert(m->val == 100);
}
