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
    while (unknown()) {
        int ev1 = unknown();
        int ev2 = unknown();
        if (ev1 < 0 || ev1 > 3 || ev2 < 0 || ev2 > 3)
            continue;
        if (((ev1 == 0) && (ev2 == 2)) || ((ev1 == 1) && (ev2 == 3)) || ((ev1 == 0) && (ev2 == 3)))
            continue;
        Node *p = malloc(sizeof(*p));
        p->event1 = ev1;
        p->event2 = ev2;
        APPEND(l,p)
    }
    Node *i = l;
    while (i != NULL) {
        //@ assert !((i->event1 == 1) && (i->event2 == 3)) || ((i->event1 == 0) && (i->event2 == 2));
        i = i->next;
    }
}
