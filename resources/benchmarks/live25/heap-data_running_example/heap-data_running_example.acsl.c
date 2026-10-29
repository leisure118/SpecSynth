#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#include <stdlib.h>
typedef struct node {
    int val;
    struct node *next;
} Node;
int main() {
    Node *p, *list = malloc(sizeof(*list));
    Node *tail = list;
    list->next = NULL;
    list->val = 10;
    //@ admit list->val >= 10 && list->val <= 20;
    //@ admit \valid(list);
    /*@
      loop invariant \valid(list);
      loop assigns tail, p, tail->next, p->next, p->val;
    */
    while (unknown()) {
        int x = unknown();
        if (x < 10 || x > 20) continue;
        p = malloc(sizeof(*p));
        //@ admit \valid(p);
        tail->next = p;
        p->next = NULL;
        p->val = x;
        //@ admit p->val >= 10 && p->val <= 20;
        tail = p;
    }
    //@ admit \forall Node *n; \valid(n) ==> n->val >= 10 && n->val <= 20;
    /*@
      loop assigns p, p->val;
    */
    while (1) {
        /*@
          loop assigns p, p->val;
        */
        for (p = list; p!= NULL; p = p->next) {
            //@ admit \valid(p);
            //@ admit p->val >= 10 && p->val <= 20;
            //@ assert(p->val <= 20 && p->val >= 10);
            if (p->val < 20) p->val++;
            else p->val /= 2;
            //@ assert(p->val >= 10 && p->val <= 20);
        }
    }
}
