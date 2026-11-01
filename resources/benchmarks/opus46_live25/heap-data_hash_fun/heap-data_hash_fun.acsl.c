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

/*@ inductive all_in_range{L}(struct node *l, integer lo, integer hi) {
      case nil{L}: \forall integer lo, hi; all_in_range(\null, lo, hi);
      case cons{L}: \forall struct node *n, integer lo, hi;
        \valid(n) ==> (integer)n->hash > lo ==> (integer)n->hash < hi ==>
        all_in_range(n->next, lo, hi) ==>
        all_in_range(n, lo, hi);
    }
*/

/*@ assigns \nothing; */
int hash_fun() { return unknown(); }

/*@
  requires \valid(list);
  assigns *list;
  ensures \valid(*list);
  ensures (*list)->hash == hash;
  ensures (*list)->next == \old(*list);
*/
void append_to_list(struct node **list, int hash);

int main() {
    struct node *list = NULL;
    int base = unknown();
    /*@
      loop invariant all_in_range(list, (integer)base, (integer)base + 100);
      loop assigns list, base;
    */
    while (unknown()) {
        if (base >= 0 && base <= 1000000) {
            base = base + 0;
            int hash = hash_fun();
            if (hash > base && hash < base + INTERVAL_SIZE)
                append_to_list(&list, hash);
        }
    }
    /*@
      loop invariant all_in_range(list, (integer)base, (integer)base + 100);
      loop assigns list;
    */
    while (list) {
        //@ assert (list->hash >= base && list->hash < base + INTERVAL_SIZE);
        list = list->next;
    }
}
