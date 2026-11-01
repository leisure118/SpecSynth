#include<limits.h>
/*@
    assigns \result;
    ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#include <stdlib.h>
#define APPEND(l,i) {i->next=l; l=i;}
typedef struct node {
    struct node *next;
    int event1;
    int event2;
} Node;

/*@ inductive valid_list_no13(Node *l) {
    case nil: valid_list_no13(\null);
    case cons: \forall Node *p;
      \valid(p) ==> valid_list_no13(p->next) ==>
      !((p->event1 == 1) && (p->event2 == 3)) ==>
      valid_list_no13(p);
} */

int main() {
    Node *l = NULL;
    /*@
      loop invariant valid_list_no13(l);
    */
    while (unknown()) {
        int ev1 = unknown();
        int ev2 = unknown();
        if (ev1 < 0 || ev1 > 3 || ev2 < 0 || ev2 > 3)
            continue;
        if (((ev1 == 0) && (ev2 == 2)) || ((ev1 == 1) && (ev2 == 3)) || ((ev1 == 0) && (ev2 == 3)))
            continue;
        Node *p = malloc(sizeof(*p));
        //@ admit \valid(p);
        //@ admit \separated(p, l);
        p->event1 = ev1;
        p->event2 = ev2;
        APPEND(l,p)
    }
    Node *i = l;
    /*@
      loop invariant valid_list_no13(i);
      loop assigns i;
    */
    while (i != NULL) {
        //@ assert !((i->event1 == 1) && (i->event2 == 3)) || ((i->event1 == 0) && (i->event2 == 2));
        i = i->next;
    }
}
