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

/*@
  axiomatic InvList {
    predicate inv_list{L}(Node *l) reads l->next, l->stock, l->order;

    axiom inv_nil{L}: inv_list(\null);

    axiom inv_construct{L}: \forall Node *n;
      \valid(n) ==> \at(n->order, L) <= \at(n->stock, L) ==>
      inv_list(\at(n->next, L)) ==> inv_list(n);

    axiom inv_destruct_valid{L}: \forall Node *n;
      inv_list(n) ==> n != \null ==> \valid(n);

    axiom inv_destruct_ord{L}: \forall Node *n;
      inv_list(n) ==> n != \null ==> \at(n->order, L) <= \at(n->stock, L);

    axiom inv_destruct_next{L}: \forall Node *n;
      inv_list(n) ==> n != \null ==> inv_list(\at(n->next, L));

    axiom inv_update{L1,L2}: \forall Node *l, *i;
      inv_list{L1}(l) ==>
      \valid{L1}(i) ==>
      \at(i->order, L2) <= \at(i->stock, L2) ==>
      \at(i->stock, L1) == \at(i->stock, L2) ==>
      (\forall Node *m; m != i ==>
        \at(m->order, L1) == \at(m->order, L2) &&
        \at(m->stock, L1) == \at(m->stock, L2) &&
        \at(m->next, L1) == \at(m->next, L2)) ==>
      inv_list{L2}(l);
  }
*/

int main() {
    Node *l = NULL;
    /*@
      loop invariant inv_list(l);
      loop assigns l;
    */
    while (unknown()) {
        int stock = unknown();
        if (stock < 0)
            continue;
        Node *p = malloc(sizeof(*p));
        //@ admit \valid(p);
        //@ admit \separated(p, l);
        p->stock = stock;
        p->order = 0;
        APPEND(l,p)
    }
    Node *i = l;
    /*@
      loop invariant inv_list(l);
      loop invariant i == \null || \valid(i);
      loop invariant i == \null || i->order <= i->stock;
      loop invariant i == \null || inv_list(i->next);
      loop assigns i, i->order, i->stock;
    */
    while (i != NULL) {
        int order = unknown();
        if (order < 0 || i->stock < order)
            continue;
        //@ admit \separated(i, i->next);
        i->order = order;
        i->stock = i->stock;
        i = i->next;
    }
    i = l;
    /*@
      loop invariant inv_list(i);
      loop assigns i;
    */
    while (i != NULL) {
        //@ assert !(i->order > i->stock);
        i = i->next;
    }
}
