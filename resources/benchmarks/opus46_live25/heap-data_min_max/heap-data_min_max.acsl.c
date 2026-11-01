#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#include <stdlib.h>
#include <limits.h>
#define APPEND(l,i) {i->next=l; l=i;}
typedef struct node {
    struct node *next;
    int val;
} Node;

/*@ axiomatic BoundedList {
  predicate bounded_list(Node *l, int min, int max);

  axiom bounded_nil: \forall int min, max;
    bounded_list(\null, min, max);

  axiom bounded_cons: \forall Node *l, int min, max;
    \valid(l) ==> min <= l->val ==> l->val <= max ==>
    bounded_list(l->next, min, max) ==> bounded_list(l, min, max);

  axiom bounded_prepend: \forall Node *n, Node *old_head, int min, max;
    \valid(n) ==> min <= n->val ==> n->val <= max ==>
    bounded_list(old_head, min, max) ==>
    n->next == old_head ==>
    bounded_list(n, min, max);

  axiom bounded_head: \forall Node *l, int min, max;
    bounded_list(l, min, max) ==> l != \null ==> min <= l->val <= max;

  axiom bounded_valid: \forall Node *l, int min, max;
    bounded_list(l, min, max) ==> l != \null ==> \valid(l);

  axiom bounded_tail: \forall Node *l, int min, max;
    bounded_list(l, min, max) ==> l != \null ==> bounded_list(l->next, min, max);

  axiom bounded_monotone: \forall Node *l, int min1, max1, min2, max2;
    bounded_list(l, min1, max1) ==> min2 <= min1 ==> max2 >= max1 ==>
    bounded_list(l, min2, max2);
}
*/

int main() {
    Node *l = NULL;
    int min = INT_MAX, max = -INT_MAX;
    /*@
      loop invariant bounded_list(l, min, max);
    */
    while (unknown()) {
        Node *p = malloc(sizeof(*p));
        //@ admit \valid(p);
        p->val = unknown();
        APPEND(l, p)
        if (min > p->val) {
            min = p->val;
        }
        if (max < p->val) {
            max = p->val;
        }
        //@ assert min <= l->val;
        //@ assert l->val <= max;
        //@ assert bounded_list(l->next, min, max);
        //@ assert bounded_list(l, min, max);
    }
    Node *i = l;
    /*@
      loop invariant bounded_list(i, min, max);
      loop assigns i;
    */
    while (i != NULL) {
        //@ assert !(i->val < min);
        //@ assert !(i->val > max);
        i = i->next;
    }
}
