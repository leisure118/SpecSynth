void order_3(int* a, int* b, int* c){
    if(*a > *b){
        int tmp = *b ; *b = *a ; *a = tmp ;
    }
    if(*a > *c){
        int tmp = *c ; *c = *a ; *a = tmp ;
    }
    if(*b > *c){
        int tmp = *b ; *b = *c ; *c = tmp ;
    }
}
void test(){
    int a1 = 5, b1 = 3, c1 = 4 ;
    if(a1 > b1){ int tmp = b1 ; b1 = a1 ; a1 = tmp ; }
    if(a1 > c1){ int tmp = c1 ; c1 = a1 ; a1 = tmp ; }
    if(b1 > c1){ int tmp = b1 ; b1 = c1 ; c1 = tmp ; }
    //@ assert a1 == 3 && b1 == 4 && c1 == 5 ;
    int a2 = 2, b2 = 2, c2 = 2 ;
    if(a2 > b2){ int tmp = b2 ; b2 = a2 ; a2 = tmp ; }
    if(a2 > c2){ int tmp = c2 ; c2 = a2 ; a2 = tmp ; }
    if(b2 > c2){ int tmp = b2 ; b2 = c2 ; c2 = tmp ; }
    //@ assert a2 == 2 && b2 == 2 && c2 == 2 ;
    int a3 = 4, b3 = 3, c3 = 4 ;
    if(a3 > b3){ int tmp = b3 ; b3 = a3 ; a3 = tmp ; }
    if(a3 > c3){ int tmp = c3 ; c3 = a3 ; a3 = tmp ; }
    if(b3 > c3){ int tmp = b3 ; b3 = c3 ; c3 = tmp ; }
    //@ assert a3 == 3 && b3 == 4 && c3 == 4 ;
    int a4 = 4, b4 = 5, c4 = 4 ;
    if(a4 > b4){ int tmp = b4 ; b4 = a4 ; a4 = tmp ; }
    if(a4 > c4){ int tmp = c4 ; c4 = a4 ; a4 = tmp ; }
    if(b4 > c4){ int tmp = b4 ; b4 = c4 ; c4 = tmp ; }
    //@ assert a4 == 4 && b4 == 4 && c4 == 5 ;
}
