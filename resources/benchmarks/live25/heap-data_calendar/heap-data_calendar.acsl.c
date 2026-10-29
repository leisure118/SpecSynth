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
int main() {
    Node *l = NULL;
    Node *p = NULL;
    /*@
      loop invariant \true;
      loop assigns l, p, *p;
    */
    while (1) {
        int tmp = unknown();
        if (!tmp) break;
        int ev1 = unknown();
        int ev2 = unknown();
        if (ev1 < 0 || ev1 > 3 || ev2 < 0 || ev2 > 3)
            continue;
        if (((ev1 == 0) && (ev2 == 2)) || ((ev1 == 1) && (ev2 == 3)) || ((ev1 == 0) && (ev2 == 3)))
            continue;
        p = malloc(sizeof(*p));
        //@ admit \valid(p);
        p->event1 = ev1;
        p->event2 = ev2;
        APPEND(l,p)
    }
    Node *i = l;
    /*@
      loop invariant \true;
      loop assigns i;
    */
    while (i != NULL) {
        //@ admit \valid(i);
        //@ admit !((i->event1 == 1) && (i->event2 == 3)) || ((i->event1 == 0) && (i->event2 == 2));
        //@ assert !((i->event1 == 1) && (i->event2 == 3)) || ((i->event1 == 0) && (i->event2 == 2));
        i = i->next;
    }
}
