;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Take snapshots and recognize patterns simultaneously while stimulus is visible
;;; During the mask stage. rehearse the disc
;;; After mask disappear, start to do the responses
;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(clear-all)

(define-model vs-fovea
    (sgp :esc t :er nil :bll 0.5 :ol t :ans 0.5 :rt 0 :ncnar nil :mas 1.6 :randomize-time t)
    (sgp :lf 1 :incremental-mouse-moves nil :viewing-distance 23.6 :pixels-per-inch 86 )
    (sgp :show-focus t :auto-attend t :needs-mouse t)
    (sgp :cursor-fitts-coeff 0.4 :default-target-width 35)
    (sgp :declarative-num-finsts 15  :declarative-finst-span 20)
    ; (sgp :visual-attention-latency 0.05)
    ; (sgp :trace-detail low)
    (sgp :trace-detail medium)
    ; (sgp :trace-detail high)

    ; (sgp :v nil :cmdt nil)


    (chunk-type reproduce state tar-x-slot tar-y-slot tar-loc total-remain group-remain tar-dot next-tar-is-ready click-finish-state click-prepared)
    (chunk-type disc type x y)
    (chunk-type (snapshot (:include visual-object)) type-tag slot_1 slot_2 slot_3 slot_4 slot_5 slot_6 slot_7 slot_8 slot_9)
    (chunk-type cross cross-slot)
    (chunk-type mask mask-slot)
    (chunk-type preparation type-tag snapshot)


    (define-chunks
        (START) (FIXATE-ON-MARK) (WAIT-SCENE-CHANGE) (ATTEND-TO-STIMULUS) (CHECK-STIMLUS-STATUS)
        (REHEARSAL-SNAPSHOT) (KEEP-SNAPSHOT) (ATTEND-TO-SCREEN) (WAIT-MASK-DISAPPEAR) (START-REPRODUCE-DOT)
        (RETRIEVE-DOT) (END) (PREPARE-MOVE-MOUSE) (MOVING-MOUSE) (START-CLICK-MOUSE) (SKIP-FORGOTTEN-GET-NEXT)
        (GET-NEXT-DOT) (MOVE-MOUSE) (MOVING-ATTENTION)
        (REHEARSAL-DISC) (DISC-CHUNK) (SNAPSHOT)

        (RETAIN-FORGOTTEN-DISC) (RETRY-UNSURE-DISC) (MOVE-MOUSE-UNSURE) (START-CLICK-MOUSE-UNSURE)
        (GET-NEXT-UNSURE-DISC) (UPDATE-UNSURE-DISC-NAME)
    )
    (add-dm
        (goal isa reproduce state start next-tar-is-ready nil click-finish-state nil click-prepared nil)
    )

    (goal-focus goal)

    (P find-fixation-cross-location
        =goal>
            ISA                 reproduce
            state               start
        ?visual>
            state               free
    ==>
        +visual-location>
        =goal>
            ISA                 reproduce
            state               fixate-on-mark
    )

    (P move-eye-to-cross-mark
        =goal>
            ISA                 reproduce
            state               fixate-on-mark
        =visual-location>
        ?visual>
            state               free
    ==>
        +visual>
            isa                 move-attention
            screen-pos          =visual-location
        =goal>
            ISA                 reproduce
            state               wait-scene-change
    )

    ;;; waiting for the visicon changes
    (P find-stimulus-appeared
        =goal>
            ISA                 reproduce
            state               wait-scene-change
        =visual-location>
    ==>
        !eval!                  ("create-chunk-tree" =visual-location)
        !bind!                  =total-num ("get-remain-disc-num")
        =goal>
            ISA                 reproduce
            state               attend-to-stimulus
            total-remain        =total-num
    )

    (P attend-to-stimulus
        =goal>
            ISA                 reproduce
            state               attend-to-stimulus
        ?visual>
            state               free
    ==>
        ; !eval!                  ("update-snapshot-activations" =visual-location)
        +visual-location>
            attended            nil
        =goal>
            ISA                 reproduce
            state               moving-attention
    )

    (P take-snapshot-using-visual-location
        =goal>
            ISA                 reproduce
            state               moving-attention
        ?visual-location>
            state               free
        =visual-location>
    ==>
        !eval!                  ("update-snapshot-activations" =visual-location)
        =goal>
            ISA                 reproduce
            state               check-stimlus-status
    )

    (P find-stimulus-still-visiable
        =goal>
            ISA                 reproduce
            state               check-stimlus-status
        ?visual>
            state               free
        =visual>
            value               =value
        !eval!                  (string= =value "dot")
        ; =visual-location>
    ==>
        ; !eval!                  ("update-snapshot-activations" =visual-location)
        =goal>
            ISA                 reproduce
            state               attend-to-stimulus
    )

    (P find-mask-appear
        =goal>
            ISA                 reproduce
            state               check-stimlus-status
        ?visual>
            state               free
        =visual>
            value               =value
        !eval!                  (string= =value "mask")
        ?imaginal>
            state               free
    ==>
        -imaginal>
        =goal>
            ISA                 reproduce
            state               rehearsal-disc
    )

    (P find-stimulus-disappear
        =goal>
            ISA                 reproduce
            state               check-stimlus-status
        ?visual>
            state               free
            state               error
            ; buffer              failure
        ?imaginal>
            state               free
    ==>
        ; !eval!                  (sdp-fct (list *dot-chunk-names* :activation))
        -imaginal>
        =goal>
            ISA                 reproduce
            state               rehearsal-disc
    )

    (P rehearsal-disc-during-mask
        =goal>
            ISA                 reproduce
            state               rehearsal-disc
        ?retrieval>
            state               free
    ==>
        +retrieval>
            ISA                 disc
            type                disc-chunk
            :recently-retrieved nil
        =goal>
            ISA                 reproduce
            state               attend-to-screen
    )



    (P rehearsal-snapshot-during-mask
        =goal>
            ISA                 reproduce
            state               rehearsal-snapshot
        ?retrieval>
            state               free
    ==>
        +retrieval>
            ISA                 snapshot
            type-tag            snapshot
        +visual-location>
        =goal>
            ISA                 reproduce
            state               keep-snapshot
    )

    (P rehearsal-snapshot-failed
        =goal>
            ISA                 reproduce
            state               keep-snapshot
        ?retrieval>
            state               free
            buffer              failure
    ==>
        +retrieval>
            ISA                 snapshot
            type-tag            snapshot
        +visual-location>
        =goal>
            ISA                 reproduce
            state               keep-snapshot
    )

    (P put-snapshot-into-imaginal
        =goal>
            ISA                 reproduce
            state               keep-snapshot
        ?retrieval>
            state               free
            - buffer              failure
        ?imaginal>
            state               free
        =retrieval>
    ==>
        +imaginal>              =retrieval
        ; +visual-location>
        =goal>
            ISA                 reproduce
            state               attend-to-screen
    )

    (P check-screen
        =goal>
            ISA                 reproduce
            state               attend-to-screen
        ?visual>
            state               free
    ==>
        +visual-location>
        =goal>
            ISA                 reproduce
            state               wait-mask-disappear
    )

    (P find-mask-still-visiable
        =goal>
            ISA                 reproduce
            state               wait-mask-disappear
        ?visual>
            state               free
        =visual>
            value               =value
        !eval!                  (string= =value "mask")
    ==>
        =goal>
            ISA                 reproduce
            state               rehearsal-disc
    )


    (P find-mask-disappear-scene-change
        =goal>
            ISA                 reproduce
            state               wait-mask-disappear
        ?visual>
            buffer              failure
    ==>
        !eval!                  (reset-declarative-finsts)
        =goal>
            ISA                 reproduce
            state               retrieve-dot
    )

    (P find-mask-disappear
        =goal>
            ISA                 reproduce
            state               wait-mask-disappear
        ?visual-location>
            buffer              failure
    ==>
        ; !eval!                  ("label_stimulation_as_validate")
        !eval!                  (reset-declarative-finsts)

        =goal>
            ISA                 reproduce
            state               retrieve-dot
    )



    ; (P get-next-target-dot
    ;     =goal>
    ;         ISA                 reproduce
    ;         state               get-next-dot
    ;         total-remain        =total-num
    ;     !eval!                  (> =total-num 0)
    ;     ; =visual-location>
    ; ==>
    ;     ; !bind!                  =next-disc ("get-next-disc-nnf" =visual-location)
    ;     !bind!                  =next-disc ("get-highest-activated-disc")
    ;     !bind!                  =new-total-num ("get-remain-disc-num")
    ;     =goal>
    ;         ISA                 reproduce
    ;         state               retrieve-dot
    ;         total-remain        =new-total-num
    ;         tar-dot             =next-disc
    ; )


    (P retrieve-dot-from-dm
        =goal>
            ISA                 reproduce
            state               retrieve-dot
            ; tar-dot             =tar-dot
        ?retrieval>
            state               free
    ==>
        +retrieval>
            :recently-retrieved nil
            type                disc-chunk
        =goal>
            ISA                 reproduce
            state               prepare-move-mouse
    )

    (P cant-remember-dot
        =goal>
            ISA                 reproduce
            state               prepare-move-mouse
        ?retrieval>
            state               free
            buffer              failure
    ==>
        =goal>
            ISA                 reproduce
            state               skip-forgotten-get-next
    )


    ; (P skip-forgotten-disc
    ;     =goal>
    ;         ISA                 reproduce
    ;         state               skip-forgotten-get-next
    ;         total-remain        =total-num
    ;     !eval!                  (> =total-num 0)
    ;     ; ?imaginal>
    ;         ; state               free
    ; ==>
    ;     ; -imaginal>
    ;     !bind!                  =next-disc ("get-highest-activated-disc")
    ;     !bind!                  =new-total-num ("get-remain-disc-num")
    ;     =goal>
    ;         ISA                 reproduce
    ;         state               retrieve-dot
    ;         total-remain        =new-total-num
    ;         tar-dot             =next-disc
    ; )

    (P retrieve-dot-success
        =goal>
            ISA                 reproduce
            state               prepare-move-mouse
        ?retrieval>
            state               free
            - buffer            failure
        =retrieval>
            x                   =x-coord
            y                   =y-coord
    ==>
        !bind!                  =loc ("create-visual-location-chunk" =x-coord =y-coord)
        =goal>
            ISA                 reproduce
            state               move-mouse
            tar-loc             =loc
            next-tar-is-ready   t
    )

    (P move-mouse-to-dot
        =goal>
            ISA                 reproduce
            state               move-mouse
            tar-loc             =tar-loc
        ?manual>
            state               free
        ?visual>
            state               free
    ==>
        +manual>
            isa                 move-cursor
            loc                 =tar-loc
        +visual>
            isa                 move-attention
            screen-pos          =tar-loc
        =goal>
            ISA                 reproduce
            state               moving-mouse
            next-tar-is-ready   nil
            click-finish-state  nil
            click-prepared      nil
    )

    ; (P get-next-target-dot-during-mouse-moving
    ;     =goal>
    ;         ISA                 reproduce
    ;         state               moving-mouse
    ;         next-tar-is-ready   nil
    ;         total-remain        =total-num
    ;         tar-loc             =tar-loc
    ;     !eval!                  (> =total-num 0)
    ;     ; =visual-location>
    ;     ?retrieval>
    ;         state               free
    ; ==>
    ;     ; !bind!                  =next-disc ("get-next-disc-nnf" =tar-loc)
    ;     ; !bind!                  =new-total-num ("get-remain-disc-num")
    ;     ; +retrieval>             =next-disc
    ;     +retrieval>
    ;         :recently-retrieved  nil
    ;         type                disc-chunk
    ;     =goal>
    ;         ISA                 reproduce
    ;         state               moving-mouse
    ;         total-remain        =new-total-num
    ;         tar-dot             =next-disc
    ; )

    (P get-next-target-dot-during-mouse-moving
        =goal>
            ISA                 reproduce
            state               moving-mouse
            next-tar-is-ready   nil
        ; =visual-location>
        ?retrieval>
            state               free
    ==>
        +retrieval>
            :recently-retrieved  nil
            type                disc-chunk
        =goal>
            ISA                 reproduce
            state               moving-mouse
    )

    (P retrieve-dot-success-during-mouse-moving
        =goal>
            ISA                 reproduce
            state               moving-mouse
        ?retrieval>
            state               free
            - buffer            failure
        =retrieval>
            x                   =x-coord
            y                   =y-coord
    ==>
        !bind!                  =loc ("create-visual-location-chunk" =x-coord =y-coord)
        =goal>
            ISA                 reproduce
            state               moving-mouse
            tar-loc             =loc
            next-tar-is-ready   t
    )



    (P cant-get-anymore-dot-during-mouse-moving
        =goal>
            ISA                 reproduce
            state               moving-mouse
            total-remain        =total-num
        ?retrieval>
            state               free
            buffer              failure
    ==>
        =goal>
            ISA                 reproduce
            state               end
    )

    (P prepare-click
        =goal>
            ISA                 reproduce
            state               moving-mouse
            click-prepared      nil
        ?manual>
            execution           busy
    ==>
        +manual>
            isa                 prepare
            style               punch
            hand                right
            finger              index
        =goal>
            ISA                 reproduce
            state               moving-mouse
            click-prepared      t
    )

    (P click-on-target
        =goal>
            ISA                 reproduce
            state               moving-mouse
            click-finish-state  nil
        ?manual>
           state                free
    ==>
        +manual>
           ; isa                  click-mouse
           isa                  execute
        =goal>
            ISA                 reproduce
            state               moving-mouse
            click-finish-state  t

    )

    (P ready-to-do-next-mouse-movement
        =goal>
            ISA                 reproduce
            state               moving-mouse
            click-finish-state  t
            next-tar-is-ready   t
        ?manual>
           state                free
    ==>
        =goal>
            ISA                 reproduce
            state               move-mouse
    )

    (P find-forgot-disc-is-the-last
        =goal>
            ISA                 reproduce
            state               skip-forgotten-get-next
            total-remain        =total-num
        !eval!                  (= =total-num 0)
    ==>
        =goal>
            ISA                 reproduce
            state               end
    )

    (P response-finished
        =goal>
            ISA                 reproduce
            state               start-reproduce-dot
            total-remain        =total-num
        !eval!                  (= =total-num 0)
    ==>
        =goal>
            ISA                 reproduce
            ; state               retry-unsure-disc
            state               end
    )

    (P response-finished-after-mouse-moving
        =goal>
            ISA                 reproduce
            state               moving-mouse
            click-finish-state  t
            next-tar-is-ready   nil
            total-remain        =total-num
        !eval!                  (= =total-num 0)
    ==>
        =goal>
            ISA                 reproduce
            state               end
    )

)
