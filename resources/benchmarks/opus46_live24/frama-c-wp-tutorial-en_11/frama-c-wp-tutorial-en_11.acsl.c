#include<limits.h>
/*@
    logic integer ax_b(integer a, integer x, integer b) = a * x + b;
*/
/*@
  requires INT_MIN <= 3 * x + 4;
  requires 3 * x + 4 <= INT_MAX;
  assigns \nothing;
  ensures \result == 3 * x + 4;
*/
int restricted(int x){
    return 3*x + 4;
}
int main(){
    int x = 10;
    int result = restricted(x);
    //@ assert result == 34;
    return 0;
}