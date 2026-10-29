#include<limits.h>
/*@
    logic integer ax_b(integer a, integer x, integer b) = a * x + b;
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