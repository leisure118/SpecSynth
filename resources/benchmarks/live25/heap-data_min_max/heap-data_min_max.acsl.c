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
/*@ inductive all_in_range{L}(Node *root, int low, int high) {
  case nil_range{L}: \forall Node *r, int l, int h; r == \null ==> all_in_range(r, l, h);
  case cons_range{L}: \forall Node *r, int l, int h;
    \valid(r) && l <= r->val <= h && all_in_range(r->next, l, h) ==> all_in_range(r, l, h);
}
*/
int main() {
    Node *l = NULL;
    int min = INT_MAX, max = -INT_MAX;
    Node *p;
    /*@
      loop invariant all_in_range(l, min, max);
      loop assigns l, min, max, p, *p;
    */
    while (unknown()) {
        p = malloc(sizeof(*p));
        p->val = unknown();
        APPEND(l, p)
        if (min > p->val) {
            min = p->val;
        }
        if (max < p->val) {
            max = p->val;
        }
    }
    Node *i = l;
    /*@
      loop invariant all_in_range(i, min, max);
      loop assigns i;
    */
    while (i != NULL) {
        //@ assert !(i->val < min);
        //@ assert !(i->val > max);
        i = i->next;
    }
}
