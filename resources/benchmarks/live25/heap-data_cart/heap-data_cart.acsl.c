#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#include <stdlib.h>
#define APPEND(l,i) {i->next=l; l=i;}
typedef struct node {
    struct node *next;
    int stock;
    int order;
} Node;
int main() {
    Node *l = NULL;
    while (unknown()) {
        int stock = unknown();
        if (stock < 0)
            continue;
        Node *p = malloc(sizeof(*p));
        /*@
          admit \valid(p);
        */
        p->stock = stock;
        p->order = 0;
        APPEND(l,p)
    }
    /*@
      admit l != NULL ==> l->order <= l->stock;
    */
    Node *i = l;
    /*@
      loop invariant i != NULL ==> i->order <= i->stock;
    */
    while (i != NULL) {
        int order = unknown();
        /*@
          admit i->stock >= 0;
        */
        if (order < 0 || i->stock < order)
            continue;
        i->order = order;
        i->stock = i->stock;
        i = i->next;
    /*@
      admit i == NULL || i->order <= i->stock;
    */
    }
    /*@ admit \valid(l) || l == NULL; */
    /*@ admit \forall Node *n; \valid(n) ==> (n->stock >= 0 && n->order <= n->stock); */
    i = l;
    /*@
      loop invariant i != NULL ==> i->order <= i->stock;
      loop assigns i;
    */
    while (i != NULL) {
        /*@
          admit \valid(i);
        */
        //@ assert !(i->order > i->stock);
        i = i->next;
    /*@
      admit i == NULL || i->order <= i->stock;
    */
    }
}
