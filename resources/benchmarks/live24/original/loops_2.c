#include <stdlib.h>
int sum(char n) {
    int s = 0;
    char k = 0;
    while(k <= n) {    
        s = s + (int)k;
        k = k + 1;
    }
    //@ assert s == (int)((n+1)*(n)/2);
    return (int)s;
}
int main() {
    int s = sum(5);
    //@ assert s == 15;
}