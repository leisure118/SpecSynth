#include<limits.h>
/*@
    logic integer ax_b(integer a, integer x, integer b) = a * x + b;
*/
/*@
  requires -2147483648 <= ax_b(3, x, 4) <= 2147483647;
  ensures \result == ax_b(3, x, 4);
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