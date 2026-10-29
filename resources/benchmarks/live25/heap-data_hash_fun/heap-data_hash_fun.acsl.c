#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#include <stdlib.h>
#define INTERVAL_SIZE 100
struct node {
    int hash;
    struct node *next;
};
/*@
  predicate all_in_range{L}(struct node *l, int b) =
    l == \null ? \true :
    (\valid(l) && l->hash >= b && l->hash < b + 100 && all_in_range(l->next, b));
*/
/*@ assigns \nothing; */
int hash_fun() { return unknown(); }
int main() {
    struct node *list = NULL;
    int base = unknown();
    /*@
      loop invariant all_in_range(list, base);
      loop invariant \at(base, LoopEntry) == base;
      loop assigns base, list, list->next, list->hash;
    */
    while (unknown()) {
        if (base >= 0 && base <= 1000000) {
            base = base + 0;
            int hash = hash_fun();
            if (hash > base && hash < base + INTERVAL_SIZE) {
                struct node *node = malloc(sizeof(*node));
                //@ admit \valid(node);
                struct node *old_list = list;
                list = node;
                list->next = old_list;
                list->hash = hash;
                //@ admit all_in_range(list, base);
            }
        }
    }
    /*@
      loop invariant all_in_range(list, base);
      loop assigns list;
    */
    while (list) {
        //@ assert (list->hash >= base && list->hash < base + INTERVAL_SIZE);
        list = list->next;
    }
}
