#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#include <stdlib.h>
#define LOW -1
#define HIGH 1
struct node {
    int expected_list;
    int value;
    struct node *next;
};
void append_to_list(struct node **list, int val, int exp) {
    struct node *node = malloc(sizeof(*node));
    node->next = *list;
    node->value = val;
    node->expected_list = exp;
    *list = node;
}
struct node *create_list() {
    struct node *list = NULL;
    while (unknown()) {
        int v = unknown();
        if (v < 0)
            append_to_list(&list, v, LOW);
        else 
            append_to_list(&list, v, HIGH);
    }
    return list;
}
int main() {
    struct node *list = create_list();
    struct node *low = NULL;
    struct node *high = NULL;
    struct node *p = list;
    while (p) {
        struct node *l = p->value >= 0 ? high : low;
        struct node *next = p->next;
        p->next = l;
        l = p;
        p = next;
    }
    while (low) {
        //@ assert(low->expected_list == LOW);
        low = low->next;
    }
    while (high) {
        //@ assert(high->expected_list == HIGH);
        high = high->next;
    }
}
