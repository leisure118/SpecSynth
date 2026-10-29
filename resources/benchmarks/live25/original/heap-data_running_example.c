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
    while (unknown()) {
        int x = unknown();
        if (x < 10 || x > 20) continue;
        p = malloc(sizeof(*p));
        tail->next = p;
        p->next = NULL;
        p->val = x;
        tail = p;
    }
    while (1) {
        for (p = list; p!= NULL; p = p->next) {
            //@ assert(p->val <= 20 && p->val >= 10);
            if (p->val < 20) p->val++;
            else p->val /= 2;
        }
    }
}
