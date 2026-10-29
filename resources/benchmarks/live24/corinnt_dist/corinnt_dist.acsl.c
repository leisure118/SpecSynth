#include <limits.h>
/*@
  assigns \nothing;
  ensures \result >= 0;
  ensures \result == (a < b ? b - a : a - b);
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