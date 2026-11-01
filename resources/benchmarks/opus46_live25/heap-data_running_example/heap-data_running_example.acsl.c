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

/*@
  inductive all_in_range(Node *p) {
    case nil: all_in_range(\null);
    case cons: \forall Node *p;
      \valid(p) ==> 10 <= p->val <= 20 ==>
      all_in_range(p->next) ==> all_in_range(p);
  }
*/

int main() {
    Node *p, *list = malloc(sizeof(*list));
    Node *tail = list;
    //@ admit \valid(list);
    list->next = NULL;
    list->val = 10;
    /*@
      loop invariant \valid(tail);
      loop invariant tail->next == \null;
      loop invariant all_in_range(list);
      loop assigns p, tail, tail->next;
    */
    while (unknown()) {
        int x = unknown();
        if (x < 10 || x > 20) continue;
        p = malloc(sizeof(*p));
        //@ admit \valid(p);
        //@ admit \separated(p + (0 .. 0), tail + (0 .. 0));
        tail->next = p;
        p->next = NULL;
        p->val = x;
        tail = p;
    }
    /*@
      loop invariant all_in_range(list);
      loop assigns p;
    */
    while (1) {
        /*@
          loop invariant all_in_range(p);
          loop assigns p;
        */
        for (p = list; p!= NULL; p = p->next) {
            //@ assert(p->val <= 20 && p->val >= 10);
            if (p->val < 20) p->val++;
            else p->val /= 2;
        }
    }
}
