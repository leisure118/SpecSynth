#include <limits.h>
/*@
  assigns \nothing;
  ensures a < b ==> \result == b - a;
  ensures a >= b ==> \result == a - b;
*/
int distance(int a, int b) {
    if (a < b) return b - a; 
    else return a - b; 
}
int main(){
    int a = -10;
    int b = 10;
    int result = distance(a, b);
    //@ assert result == 20;
    return 0;
}