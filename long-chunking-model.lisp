;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Take snapshots and recognize patterns simultaneously while stimulus is visible
;;; During the mask stage. rehearse the chunk tree
;;; After mask disappear, start to do the responses
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(clear-all)

(define-model l-chunking
    (sgp :mas 10) ;spreading activation
    (sgp :esc t :er nil :bll 0.5 :ol t :ans 0.5 :rt 0 :ncnar nil  :randomize-time t)
    (sgp :lf 1 :incremental-mouse-moves nil :viewing-distance 23.6 :pixels-per-inch 86)
    (sgp :show-focus t :auto-attend t :needs-mouse t)
    (sgp :visual-num-finsts 10 :visual-finst-span 80)
    (sgp :declarative-num-finsts 30  :declarative-finst-span 20)
    (sgp :cursor-fitts-coeff 0.4 :default-target-width 35)
    (sgp :trace-detail low)
    ; (sgp :trace-detail medium)
    ; (sgp :trace-detail high)

    ; (sgp :v nil :cmdt nil)


    (chunk-type reproduce state found-pattern root pre-root-slot pre-root-slot-value cur-tar-root-slot rehearsing-disc next-group-slot check-screen
                          click-state next-disc-state

                          tar-x-slot tar-y-slot tar-loc total-remain group-remain tar-dot next-tar-is-ready click-finish-state click-prepared
                          tar-slot next-tar-slot-name-is-ready cur-group-finished sub-goal)
    (chunk-type disc type-tag x y)
    (chunk-type root type-tag slot1 slot2 slot3 slot4 slot5 slot6 slot7 slot8 slot9)
    (chunk-type cross cross-slot)
    (chunk-type mask mask-slot)

    (chunk-type square type-tag x1 y1 x2 y2 x3 y3 x4 y4)
    (chunk-type triangle type-tag x1 y1 x2 y2 x3 y3)
    (chunk-type disc-group type-tag size disc1 disc2 disc3 disc4 disc5 disc6)


    (define-chunks
        (root-chunk isa root type-tag root)

        (start)
        (triangle) (square) (disc-group)
        (found) (not-found) (chunk-rehearsal-finish) (chunking-root) (slot1) (slot2) (slot3) (slot4) (slot5) (slot6) (slot7)
    )
    (add-dm
        (goal isa reproduce state start root root-chunk )
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

    ;;;==============================================================
    ;;;     Stimulus state
    ;;;==============================================================

    ;;; waiting for the visicon changes
    (P find-stimulus-appeared
        =goal>
            ISA                 reproduce
            state               wait-scene-change
        =visual-location>
    ==>
        !eval!                  ("take-snapshot" =visual-location)
        ; !bind!                  =total-num ("get-remain-disc-num")
        =goal>
            ISA                 reproduce
            state               attend-to-stimulus
    )

    (P attend-to-stimulus
        =goal>
            ISA                 reproduce
            state               attend-to-stimulus
        ?visual-location>
            state               free
        ?imaginal>
            state               free
    ==>
        !eval!                  (remove-visual-finsts)
        -imaginal>
        +visual-location>
            :attended           nil
            screen-x            lowest
        =goal>
            ISA                 reproduce
            state               swifting-eye-to-first-disc
    )


    (P attended-to-most-left-disc
        =goal>
            state               swifting-eye-to-first-disc
        ?visual-location>
            state               free
        =visual-location>
        ?visual>
            state               free
        =visual>
            value               "dot"

    ==>
        !eval!                  ("get-salient-pattern" =visual-location)
        =goal>
            state               preparing-find-salient-pattern
    )

    (P browsing-stimulus-to-find-salient-pattern
        =goal>
            state               preparing-find-salient-pattern
        ?visual-location>
            state               free
    ==>
        +visual-location>
            :attended           nil
        =goal>
            state               wating-shift-attention
    )

    (P browsing-stimulus-finish
        =goal>
            state               wating-shift-attention
        ?visual-location>
            state               free
            buffer              failure
    ==>
        =goal>
            state               preparing-split-non-pattern-disc-into-group
    )

    (P check-salient-pattern
        =goal>
            state               wating-shift-attention
        ?visual-location>
            state               free
        =visual-location>
        ?visual>
            state               free
        =visual>
            value               "dot"
    ==>
        !bind!                  =found-pattern-state ("get-salient-pattern" =visual-location)
        =goal>
            state               checking-salient-pattern
            found-pattern       =found-pattern-state
    )

    (P find-pattern-failed
        =goal>
            state               checking-salient-pattern
            found-pattern       not-found
    ==>
        =goal>
            state               preparing-find-salient-pattern
    )

    (P find-pattern-success
        =goal>
            state               checking-salient-pattern
            found-pattern       found
        ?retrieval>
            state               free
    ==>
        +retrieval>
            type-tag            chunking-root
        =goal>
            state               retrieving-root-chunk
    )

    ; (P create-root-chunk
    ;     =goal>
    ;         state               creating-root-chunk
    ;     ?imaginal>
    ;         state               free
    ;     =imaginal>
    ; ==>
    ;     +imaginal>
    ;         ISA                 root
    ;         type-tag            chunking-root
    ;         slot1               =imaginal
    ;     =goal>
    ;         state               creating-root-chunk-in-imaginal
    ;         pre-root-slot       slot1
    ;         pre-root-slot-value =imaginal
    ; )

    (P retrieve-root-chunk-failed
        =goal>
            state               retrieving-root-chunk
        ?retrieval>
            buffer              failure
        ?imaginal>
            state               free
        =imaginal>
    ==>
        +imaginal>
            ISA                 root
            type-tag            chunking-root
            slot1               =imaginal
        =goal>
            state               creating-root-chunk-in-imaginal
            pre-root-slot       slot1
            pre-root-slot-value =imaginal
    )

    (P save-root-into-DM
        =goal>
            state               creating-root-chunk-in-imaginal
        ?imaginal>
            state               free
    ==>
        -imaginal>
        =goal>
            state               preparing-find-salient-pattern
    )

    (P retrieve-root-chunk-success
        =goal>
            state               retrieving-root-chunk
        ?retrieval>
            state               free
            - buffer              failure
    ==>
        =goal>
            state               finding-empty-slot-to-put-pattern
    )

    (P save-chunk-into-slot2-of-root
        =goal>
            state               finding-empty-slot-to-put-pattern
        ?retrieval>
            state               free
        =retrieval>
            slot1               =slot1-val
            ; slot2               nil
        !eval!                  ("check-if-chunk-slot-is-empty" =retrieval "slot2")
        ?imaginal>
            state               free
        =imaginal>
    ==>
        +imaginal>
            ISA                 root
            type-tag            chunking-root
            slot1               =slot1-val
            slot2               =imaginal
        =goal>
            state               putting-chunk-into-root
            pre-root-slot       slot2
            pre-root-slot-value =imaginal
    )

    (P save-chunk-into-slot3-of-root
        =goal>
            state               finding-empty-slot-to-put-pattern
        ?retrieval>
            state               free
        =retrieval>
            slot1               =slot1-val
            slot2               =slot2-val
            ; slot3               nil
        !eval!                  ("check-if-chunk-slot-is-empty" =retrieval "slot3")
        ?imaginal>
            state               free
        =imaginal>
    ==>
        +imaginal>
            ISA                 root
            type-tag            chunking-root
            slot1               =slot1-val
            slot2               =slot2-val
            slot3               =imaginal
        =goal>
            state               putting-chunk-into-root
            pre-root-slot       slot3
            pre-root-slot-value =imaginal
    )

    (P save-chunk-into-slot4-of-root
        =goal>
            state               finding-empty-slot-to-put-pattern
        ?retrieval>
            state               free
        =retrieval>
            slot1               =slot1-val
            slot2               =slot2-val
            slot3               =slot3-val
        !eval!                  ("check-if-chunk-slot-is-empty" =retrieval "slot4")
        ?imaginal>
            state               free
        =imaginal>
    ==>
        +imaginal>
            ISA                 root
            type-tag            chunking-root
            slot1               =slot1-val
            slot2               =slot2-val
            slot3               =slot3-val
            slot4               =imaginal
        =goal>
            state               putting-chunk-into-root
            pre-root-slot       slot4
            pre-root-slot-value =imaginal
    )

    (P save-chunk-into-slot5-of-root
        =goal>
            state               finding-empty-slot-to-put-pattern
        ?retrieval>
            state               free
        =retrieval>
            slot1               =slot1-val
            slot2               =slot2-val
            slot3               =slot3-val
            slot4               =slot4-val
        !eval!                  ("check-if-chunk-slot-is-empty" =retrieval "slot5")
        ?imaginal>
            state               free
        =imaginal>
    ==>
        +imaginal>
            ISA                 root
            type-tag            chunking-root
            slot1               =slot1-val
            slot2               =slot2-val
            slot3               =slot3-val
            slot4               =slot4-val
            slot5               =imaginal
        =goal>
            state               putting-chunk-into-root
            pre-root-slot       slot5
            pre-root-slot-value =imaginal
    )

    (P save-chunk-into-slot6-of-root
        =goal>
            state               finding-empty-slot-to-put-pattern
        ?retrieval>
            state               free
        =retrieval>
            slot1               =slot1-val
            slot2               =slot2-val
            slot3               =slot3-val
            slot4               =slot4-val
            slot5               =slot5-val
        !eval!                  ("check-if-chunk-slot-is-empty" =retrieval "slot6")
        ?imaginal>
            state               free
        =imaginal>
    ==>
        +imaginal>
            ISA                 root
            type-tag            chunking-root
            slot1               =slot1-val
            slot2               =slot2-val
            slot3               =slot3-val
            slot4               =slot4-val
            slot5               =slot5-val
            slot6               =imaginal
        =goal>
            state               putting-chunk-into-root
            pre-root-slot       slot6
            pre-root-slot-value =imaginal
    )

    (P save-imaginal-into-dm
        =goal>
            state               putting-chunk-into-root
        ?imaginal>
            state               free
    ==>
        -imaginal>
        =goal>
            state               preparing-split-non-pattern-disc-into-group
    )

    (P split-non-pattern-disc
        =goal>
            state               preparing-split-non-pattern-disc-into-group
            pre-root-slot       =root-slot
            pre-root-slot-value =root-slot-value
        ?retrieval>
            state               free
    ==>
        !eval!                  ("split-non-pattern-disc")
        +retrieval>
            type-tag            chunking-root
            =root-slot          =root-slot-value
        =goal>
            state               retrieving-root-chunk
    )

    (P  split-non-pattern-disc-while-root-not-exist
        =goal>
            state               preparing-split-non-pattern-disc-into-group
        !eval!                  ("check-if-chunk-slot-is-empty" =goal "pre-root-slot")
        ?imaginal>
            state               free
    ==>
        !eval!                  ("split-non-pattern-disc")
        =goal>
            state               spliting-disc
    )

    (P create-root-after-split-non-pattern-disc
        =goal>
            state               spliting-disc
        ?imaginal>
            state               free
        =imaginal>
    ==>
        +imaginal>
            ISA                 root
            type-tag            chunking-root
            slot1               =imaginal
        =goal>
            state               putting-chunk-into-root
            pre-root-slot       slot1
            pre-root-slot-value =imaginal
    )

    (P split-non-pattern-disc-finish
        =goal>
            state               retrieving-root-chunk
        ?retrieval>
            state               free
        ?imaginal>
            buffer              empty
    ==>
        =goal>
            state               preparing-moving-root-chunk
            check-screen        checking-stimulus
    )

    (P put-root-into-imaginal
        =goal>
            state               preparing-moving-root-chunk
        ?retrieval>
            state               free
            - buffer               empty
        =retrieval>
        ?imaginal>
            state               free
            ; buffer              empty
    ==>
        +imaginal>              =retrieval
        !bind!                  =cur-slot-name ("get-next-group-slot-name")
        =goal>
            state               preparing-rehearsal-while-stimulus-still-visiable
            cur-tar-root-slot   =cur-slot-name
    )

    (P retrieve-tar-group-chunk
        =goal>
            state               preparing-rehearsal-while-stimulus-still-visiable
            cur-tar-root-slot   =tar-slot
        ?retrieval>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            =tar-slot           =tar-slot-val
    ==>
        =imaginal>
        +retrieval>             =tar-slot-val
        =goal>
            state               retreiving-tar-group-chunk
    )

    (P retrieve-tar-group-chunk-success
        =goal>
            state               retreiving-tar-group-chunk
        ?retrieval>
            state               free
            - buffer              failure
    ==>
        !bind!                  =cur-slot-name ("get-next-group-slot-name")
        =goal>
            state               preparing-move-tar-chunk-to-imaginal
            cur-tar-root-slot   =cur-slot-name
    )

    ;;; check stimulus, if stimulus still visiable, save one reference to DM
    ; (P retrieve-tar-group-chunk-failed
    ;     =goal>
    ;         state               retreiving-tar-group-chunk
    ;     ?retrieval>
    ;         state               free
    ;         buffer              failure
    ; ==>
    ;     =goal>
    ;         state               inspecting-stimulus-to-enhence-pattern-memory
    ; )
    ;
    ; (P )

    (P move-retrieved-tar-group-chunk-to-imaginal
        =goal>
            state               preparing-move-tar-chunk-to-imaginal
        ?imaginal>
            state               free
        ?retrieval>
            state               free
        =retrieval>
    ==>
        +imaginal>              =retrieval
        =goal>
            state               identifying-tar-group-chunk-type
    )

    (P start-rehearsal-square
        =goal>
            state               identifying-tar-group-chunk-type
        ?imaginal>
            state               free
        =imaginal>
            type-tag            =type-tag-val
        !eval!                  (eq =type-tag-val 'square)
    ==>
        =imaginal>
        =goal>
            state               rehearsing-square-chunk
    )

    (P moving-attention-to-disc1-in-square
        =goal>
            state               rehearsing-square-chunk
        ?imaginal>
            state               free
        =imaginal>
            x1                  =screen-x
            y1                  =screen-y
        ?visual>
            state               free
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               check-disc1-square
    )

    (P find-disc1-square-still-visiable
        =goal>
            state               check-disc1-square
        ?visual>
            state               free
        =visual>
            value               "dot"
    ==>
        =goal>
            state               preparing-move-attention-to-disc2-square
    )

    (P find-disc1-square-disappeared
        =goal>
            state               check-disc1-square
        ?visual>
            state               free
            buffer              failure
    ==>
        =goal>
            state               stimulus-disappeared
    )

    (P moving-attention-to-disc2-in-square
        =goal>
            state               preparing-move-attention-to-disc2-square
        ?imaginal>
            state               free
        =imaginal>
            x2                  =screen-x
            y2                  =screen-y
        ?visual>
            state               free
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               check-disc2-square
    )

    (P find-disc2-square-still-visiable
        =goal>
            state               check-disc2-square
        ?visual>
            state               free
        =visual>
            value               "dot"
    ==>
        =goal>
            state               preparing-move-attention-to-disc3-square
    )

    (P find-disc2-square-disappeared
        =goal>
            state               check-disc2-square
        ?visual>
            state               free
            buffer              failure
    ==>
        =goal>
            state               stimulus-disappeared
    )

    (P moving-attention-to-disc3-in-square
        =goal>
            state               preparing-move-attention-to-disc3-square
        ?imaginal>
            state               free
        =imaginal>
            x3                  =screen-x
            y3                  =screen-y
        ?visual>
            state               free
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               check-disc3-square
    )

    (P find-disc3-square-still-visiable
        =goal>
            state               check-disc3-square
        ?visual>
            state               free
        =visual>
            value               "dot"
    ==>
        =goal>
            state               preparing-move-attention-to-disc4-square
    )

    (P find-disc3-square-disappeared
        =goal>
            state               check-disc3-square
        ?visual>
            state               free
            buffer              failure
    ==>
        =goal>
            state               stimulus-disappeared
    )

    (P moving-attention-to-disc4-in-square
        =goal>
            state               preparing-move-attention-to-disc4-square
        ?imaginal>
            state               free
        =imaginal>
            x4                  =screen-x
            y4                  =screen-y
        ?visual>
            state               free
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" (+ =screen-x 10) (+ =screen-y 10))
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               check-disc4-square
    )

    (P find-disc4-square-still-visiable
        =goal>
            state               check-disc4-square
        ?visual>
            state               free
        =visual>
            value               "dot"
    ==>
        =goal>
            state               preparing-retrieve-root-for-next-pattern
    )

    (P find-disc4-square-disappeared
        =goal>
            state               check-disc4-square
        ?visual>
            state               free
            buffer              failure
    ==>
        =goal>
            state               stimulus-disappeared
    )

    (P start-rehearsal-triangle
        =goal>
            state               identifying-tar-group-chunk-type
        ?imaginal>
            state               free
        =imaginal>
            type-tag            =type-tag-val
        !eval!                  (eq =type-tag-val 'triangle)
    ==>
        =imaginal>
        =goal>
            state               rehearsing-triangle-chunk
    )

    (P moving-attention-to-disc1-in-triangle
        =goal>
            state               rehearsing-triangle-chunk
        ?imaginal>
            state               free
        =imaginal>
            x1                  =screen-x
            y1                  =screen-y
        ?visual>
            state               free
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               check-disc1-triangle
    )

    (P find-disc1-triangle-still-visiable
        =goal>
            state               check-disc1-triangle
        ?visual>
            state               free
        =visual>
            value               "dot"
    ==>
        =goal>
            state               preparing-move-attention-to-disc2-triangle
    )

    (P find-disc1-triangle-disappeared
        =goal>
            state               check-disc1-triangle
        ?visual>
            state               free
            buffer              failure
    ==>
        =goal>
            state               stimulus-disappeared
    )

    (P moving-attention-to-disc2-in-triangle
        =goal>
            state               preparing-move-attention-to-disc2-triangle
        ?imaginal>
            state               free
        =imaginal>
            x2                  =screen-x
            y2                  =screen-y
        ?visual>
            state               free
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               check-disc2-triangle
    )

    (P find-disc12-triangle-still-visiable
        =goal>
            state               check-disc2-triangle
        ?visual>
            state               free
        =visual>
            value               "dot"
    ==>
        =goal>
            state               preparing-move-attention-to-disc3-triangle
    )

    (P find-disc2-triangle-disappeared
        =goal>
            state               check-disc2-triangle
        ?visual>
            state               free
            buffer              failure
    ==>
        =goal>
            state               stimulus-disappeared
    )

    (P moving-attention-to-disc3-in-triangle
        =goal>
            state               preparing-move-attention-to-disc3-triangle
        ?imaginal>
            state               free
        =imaginal>
            x3                  =screen-x
            y3                  =screen-y
        ?visual>
            state               free
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               check-disc3-triangle
    )

    (P find-disc13-triangle-still-visiable
        =goal>
            state               check-disc3-triangle
        ?visual>
            state               free
        =visual>
            value               "dot"
    ==>
        =goal>
            state               preparing-retrieve-root-for-next-pattern
    )

    (P find-disc3-triangle-disappeared
        =goal>
            state               check-disc3-triangle
        ?visual>
            state               free
            buffer              failure
    ==>
        =goal>
            state               stimulus-disappeared
    )

    (P start-rehearsal-disc-group
        =goal>
            state               identifying-tar-group-chunk-type
        ?imaginal>
            state               free
        =imaginal>
            type-tag            =type-tag-val
        !eval!                  (eq =type-tag-val 'disc-group)
    ==>
        =imaginal>
        !bind!                  =next-slot-name ("get-next-in-group-slot" =imaginal)
        =goal>
            state               rehearsing-group-chunk
            next-group-slot     =next-slot-name
    )

    (P retrieve-next-disc-in-group
        =goal>
            state               rehearsing-group-chunk
            next-group-slot     =next-slot-name
        ?imaginal>
            state               free

        =imaginal>
            =next-slot-name     =disc
        ?retrieval>
            state               free
    ==>
        =imaginal>
        +retrieval>             =disc
        =goal>
            state               rehearsing-group-disc
            rehearsing-disc     rehearsing-group-disc
    )

    (P retrieve-ingroup-disc
        =goal>
            rehearsing-disc     rehearsing-group-disc
        ?retrieval>
            state               free
            - buffer            failure
        =retrieval>
            x                   =screen-x
            y                   =screen-y
        ?visual>
            state               free
    ==>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            rehearsing-disc     moving-attention
    )

    (P retrieve-ingroup-disc-failure
        =goal>
            rehearsing-disc     rehearsing-group-disc
        ?retrieval>
            state               free
            buffer              failure
    ==>
        =goal>
            rehearsing-disc     disc-rehearsal-finish
    )

    (P find-ingroup-disc-still-visiable
        =goal>
            rehearsing-disc     moving-attention
        ?visual>
            state               free
        =visual>
            value               "dot"
    ==>
        =goal>
            rehearsing-disc     disc-rehearsal-finish
    )

    ; (P find-ingroup-disc-disappeared
    ;     =goal>
    ;         rehearsing-disc     moving-attention
    ;     ?visual>
    ;         state               free
    ;         buffer              failure
    ; ==>
    ;     =goal>
    ;         state               stimulus-disappeared
    ; )

    (P start-rehearsing-next-disc
        =goal>
            state               rehearsing-group-disc
            rehearsing-disc     disc-rehearsal-finish
        ?imaginal>
            state               free
        =imaginal>
    ==>
        =imaginal>
        !bind!                  =next-slot-name ("get-next-in-group-slot" =imaginal)
        =goal>
            state               rehearsing-group-chunk
            next-group-slot     =next-slot-name
    )

    (P rehsearse-current-group-finished
        =goal>
            state               rehearsing-group-chunk
            next-group-slot     chunk-rehearsal-finish
    ==>
        =goal>
            state               preparing-retrieve-root-for-next-pattern
    )

    (P retrieve-root-for-rehsearse
        =goal>
            state               preparing-retrieve-root-for-next-pattern
            pre-root-slot       =root-slot
            pre-root-slot-value =root-slot-value
        ?retrieval>
            state               free
    ==>
        +retrieval>
            type-tag            chunking-root
            =root-slot          =root-slot-value
        =goal>
            state               preparing-moving-root-chunk
    )

    (P find-stimulus-disappeared
        =goal>
            check-screen        checking-stimulus
        ?visual>
            state               free
            scene-change        t
    ==>
        +visual>
            cmd                 clear-scene-change
        =goal>
            state               found-stimulus-disappeared
            check-screen        stimulus-disappeared
            rehearsing-disc     end
    )

    ;;;==============================================================
    ;;;     Mask state
    ;;;==============================================================


    (P start-to-rehearsal-during-mask
        =goal>
            state               found-stimulus-disappeared
            pre-root-slot       =root-slot
            pre-root-slot-value =root-slot-value
        ?retrieval>
            state               free
    ==>
        +retrieval>
            type-tag            chunking-root
            =root-slot          =root-slot-value
        =goal>
            state               retrieving-root-during-mask
            check-screen        checking-mask
    )

    (P find-mask-disappeared
        =goal>
            check-screen        checking-mask
        ?visual>
            scene-change        t
    ==>
        !eval!                  ("reset-root-slot-index")
        !eval!                  (reset-declarative-finsts)
        =goal>
            check-screen        mask-disappeared
            state               response-from-root
    )


    (P move-root-to-imaginal-during-mask
        =goal>
            state               retrieving-root-during-mask
        ?retrieval>
            state               free
            - buffer               empty
        =retrieval>
        ?imaginal>
            state               free
    ==>
        +imaginal>              =retrieval
        !bind!                  =cur-slot-name ("get-next-group-slot-name")
        =goal>
            state               preparing-retrieve-group-during-mask
            cur-tar-root-slot   =cur-slot-name
    )

    (P retrieve-group-during-mask
        =goal>
            state               preparing-retrieve-group-during-mask
            cur-tar-root-slot   =tar-slot
            check-screen        checking-mask
        ?retrieval>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            =tar-slot           =tar-slot-val
    ==>
        =imaginal>
        +retrieval>             =tar-slot-val
        !bind!                  =cur-slot-name ("get-next-group-slot-name")
        =goal>
            state               retrieving-group-during-mask
            cur-tar-root-slot   =cur-slot-name
    )

    ; (P stop-retrieve-after-mask-disappeared
    ;     =goal>
    ;         state               preparing-retrieve-group-during-mask
    ;         check-screen        mask-disappeared
    ; ==>
    ;     =goal>
    ;         state               response-from-root
    ; )

    (P retrieve-group-during-mask-success
        =goal>
            state               retrieving-group-during-mask
        ?retrieval>
            state               free
            - buffer              failure
    ==>
        =goal>
            state               identifying-group-type-during-mask
    )

    ;;; if failed, skip and retrieve next group
    (P retrieve-tar-group-chunk-failed-during-mask
        =goal>
            state               retrieving-group-during-mask
        ?retrieval>
            state               free
            buffer              failure
    ==>
        =goal>
            state               preparing-retrieve-group-during-mask
    )

    (P  find-retrieved-is-pattern-chunk-during-mask
        =goal>
            state               identifying-group-type-during-mask
        ?retrieval>
            state               free
        =retrieval>
            type-tag            =type-tag-val
        !eval!                  (not (eq =type-tag-val 'disc-group))
    ==>
        =retrieval>
        =goal>
            state               preparing-retrieve-group-during-mask
    )

    (P  find-retrieved-is-group-chunk-during-mask
        =goal>
            state               identifying-group-type-during-mask
        ?retrieval>
            state               free
        =retrieval>
            type-tag            =type-tag-val
        !eval!                  (eq =type-tag-val 'disc-group)
    ==>
        =retrieval>
        =goal>
            state               preparing-move-chunk-to-imaginal-during-mask
    )

    (P move-retrieved-group-to-imaginal-during-mask
        =goal>
            state               preparing-move-chunk-to-imaginal-during-mask
        ?imaginal>
            state               free
        ?retrieval>
            state               free
        =retrieval>
    ==>
        +imaginal>              =retrieval
        =goal>
            state               moving-chunk-to-imaginal-during-mask
    )

    (P rehearsal-in-group-disc-during-mask
        =goal>
            state               moving-chunk-to-imaginal-during-mask
        ?imaginal>
            state               free
        =imaginal>
    ==>
        =imaginal>
        !bind!                  =next-slot-name ("get-next-in-group-slot" =imaginal)
        =goal>
            state               preparing-rehearsing-disc-during-mask
            next-group-slot     =next-slot-name
    )

    (P retrieve-disc-in-group-during-mask
        =goal>
            state               preparing-rehearsing-disc-during-mask
            next-group-slot     =next-slot-name
        ?imaginal>
            state               free
        =imaginal>
            =next-slot-name     =disc
        ?retrieval>
            state               free
    ==>
        =imaginal>
        +retrieval>             =disc
        =goal>
            state               rehearsing-disc-during-mask
    )

    (P rehearsal-group-finished-during-mask
        =goal>
            state               preparing-rehearsing-disc-during-mask
            next-group-slot     chunk-rehearsal-finish
    ==>
        =goal>
            state               moving-chunk-to-imaginal-during-mask
    )

    (P retrieve-disc-in-group-during-mask-finished
        =goal>
            state               rehearsing-disc-during-mask
        ?retrieval>
            state               free
    ==>
        =goal>
            state               moving-chunk-to-imaginal-during-mask
    )

    ;;;==============================================================
    ;;;     Response state
    ;;;==============================================================

    (P retrieve-root-during-response
        =goal>
            state               response-from-root
            pre-root-slot       =root-slot
            pre-root-slot-value =root-slot-value
        ?retrieval>
            state               free
    ==>
        +retrieval>
            type-tag            chunking-root
            =root-slot          =root-slot-value

        =goal>
            state               retrieving-root-during-response
    )

    (P retrieve-root-success-during-response
        =goal>
            state               retrieving-root-during-response
        ?retrieval>
            state               free
            - buffer               empty
        =retrieval>
        ?imaginal>
            state               free
    ==>
        +imaginal>              =retrieval
        !bind!                  =cur-slot-name ("get-next-group-slot-name-for-response")
        =goal>
            state               preparing-retrieve-group-during-response
            cur-tar-root-slot   =cur-slot-name
    )

    (P retrieve-root-failure-during-mask
        =goal>
            state               retrieving-root-during-response
        ?retrieval>
            state               free
            buffer              failure
    ==>
        =goal>
            state               end
    )

    (P retrieve-group-during-response
        =goal>
            state               preparing-retrieve-group-during-response
            cur-tar-root-slot   =tar-slot
        !eval!                  (not (eq =tar-slot 'response-finished))
        ?retrieval>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            =tar-slot           =tar-slot-val
    ==>
        =imaginal>
        +retrieval>             =tar-slot-val
        ; !bind!                  =cur-slot-name ("get-next-group-slot-name-for-response")
        =goal>
            state               retrieving-group-during-response
            ; cur-tar-root-slot   =cur-slot-name
    )

    (P response-finished
        =goal>
            state               preparing-retrieve-group-during-response
            cur-tar-root-slot   response-finished
    ==>
        =goal>
            ; state               end
            state               preparing-retrieve-rest-disc
    )

    (P find-not-further-group-in-root
        =goal>
            state               preparing-retrieve-group-during-response
            cur-tar-root-slot   =tar-slot
        !eval!                  (not (eq =tar-slot 'response-finished))
        ?retrieval>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            =tar-slot           nil
    ==>
        =goal>
            ; state               end
            state               preparing-retrieve-rest-disc
    )

    (P retrieve-group-during-response-success
        =goal>
            state               retrieving-group-during-response
        ?retrieval>
            state               free
            - buffer              failure
        =retrieval>
        ?imaginal>
            state               free
    ==>
        +imaginal>              =retrieval
        =goal>
            state               moving-group-chunk-to-imaginal-response
    )

    (P retrieve-tar-group-chunk-failed-during-response
        =goal>
            state               retrieving-group-during-response
        ?retrieval>
            state               free
            buffer              failure
    ==>
        !bind!                  =cur-slot-name ("get-next-group-slot-name-for-response")
        =goal>
            state               preparing-retrieve-group-during-response
            cur-tar-root-slot   =cur-slot-name
    )


    (P  find-retrieved-is-triangle-chunk-during-response
        =goal>
            state               moving-group-chunk-to-imaginal-response
        ?imaginal>
            state               free
        =imaginal>
            type-tag            =type-tag-val
        !eval!                  (eq =type-tag-val 'triangle)
    ==>
        =imaginal>
        =goal>
            state               preparing-moving-to-triangle-disc1
    )

    (P  find-retrieved-is-square-chunk-during-response
        =goal>
            state               moving-group-chunk-to-imaginal-response
        ?imaginal>
            state               free
        =imaginal>
            type-tag            =type-tag-val
        !eval!                  (eq =type-tag-val 'square)
    ==>
        =imaginal>
        =goal>
            state               preparing-moving-to-square-disc1
    )

    (P  find-retrieved-is-group-chunk-during-response
        =goal>
            state               moving-group-chunk-to-imaginal-response
        ?imaginal>
            state               free
        =imaginal>
            type-tag            =type-tag-val
        !eval!                  (eq =type-tag-val 'disc-group)
    ==>
        =imaginal>
        !bind!                  =next-slot-name ("get-next-in-group-slot" =imaginal)
        =goal>
            state               preparing-retrieving-disc-ingroup-during-response
            next-group-slot     =next-slot-name
    )

    (P move-to-triangle-disc1-location-during-response
        =goal>
            state               preparing-moving-to-triangle-disc1
        ?manual>
            state               free
        ?visual>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            x1                  =screen-x
            y1                  =screen-y
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +manual>
            isa                 move-cursor
            loc                 =screen-location
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               preparing-moving-to-triangle-disc2
            click-state         moving-cursor
            next-disc-state     ready
    )

    (P move-to-triangle-disc2-location-during-response
        =goal>
            state               preparing-moving-to-triangle-disc2
            click-state         finished
            next-disc-state     ready
        ?manual>
            state               free
        ?visual>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            x2                  =screen-x
            y2                  =screen-y
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +manual>
            isa                 move-cursor
            loc                 =screen-location
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               preparing-moving-to-triangle-disc3
            click-state         moving-cursor
            next-disc-state     ready
    )

    (P move-to-triangle-disc3-location-during-response
        =goal>
            state               preparing-moving-to-triangle-disc3
            click-state         finished
            next-disc-state     ready
        ?manual>
            state               free
        ?visual>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            x3                  =screen-x
            y3                  =screen-y
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +manual>
            isa                 move-cursor
            loc                 =screen-location
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               preparing-root-for-next-group
            click-state         moving-cursor
            next-disc-state     ready
    )

    (P move-to-square-disc1-location-during-response
        =goal>
            state               preparing-moving-to-square-disc1
        ?manual>
            state               free
        ?visual>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            x1                  =screen-x
            y1                  =screen-y
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +manual>
            isa                 move-cursor
            loc                 =screen-location
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               preparing-moving-to-square-disc2
            click-state         moving-cursor
            next-disc-state     ready
    )

    (P move-to-square-disc2-location-during-response
        =goal>
            state               preparing-moving-to-square-disc2
            click-state         finished
            next-disc-state     ready
        ?manual>
            state               free
        ?visual>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            x2                  =screen-x
            y2                  =screen-y
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +manual>
            isa                 move-cursor
            loc                 =screen-location
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               preparing-moving-to-square-disc3
            click-state         moving-cursor
            next-disc-state     ready
    )

    (P move-to-square-disc3-location-during-response
        =goal>
            state               preparing-moving-to-square-disc3
            click-state         finished
            next-disc-state     ready
        ?manual>
            state               free
        ?visual>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            x3                  =screen-x
            y3                  =screen-y
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +manual>
            isa                 move-cursor
            loc                 =screen-location
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               preparing-moving-to-square-disc4
            click-state         moving-cursor
            next-disc-state     ready
    )

    (P move-to-square-disc4-location-during-response
        =goal>
            state               preparing-moving-to-square-disc4
            click-state         finished
            next-disc-state     ready
        ?manual>
            state               free
        ?visual>
            state               free
        ?imaginal>
            state               free
        =imaginal>
            x4                  =screen-x
            y4                  =screen-y
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +manual>
            isa                 move-cursor
            loc                 =screen-location
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =goal>
            state               preparing-root-for-next-group
            click-state         moving-cursor
            next-disc-state     ready
    )

    (P reproduce-group-finished
        =goal>
            state               preparing-retrieving-disc-ingroup-during-response
            next-group-slot     chunk-rehearsal-finish
    ==>
        =goal>
            state               preparing-root-for-next-group
    )

    (P retrieve-ingroup-disc-during-response
        =goal>
            state               preparing-retrieving-disc-ingroup-during-response
            next-group-slot     =next-slot-name
        ?imaginal>
            state               free
        =imaginal>
            =next-slot-name     =disc-name
        ?retrieval>
            state               free
    ==>
        =imaginal>
        +retrieval>             =disc-name
        =goal>
            state               retrieving-next-disc-during-response
            ; click-state         moving-cursor
            ; next-disc-state     retrieving
    )

    (P retrieve-ingroup-disc-during-response-success
        =goal>
            state               retrieving-next-disc-during-response
            ; click-state         finished
        ?retrieval>
            state               free
            - buffer              failure
        ?manual>
            state               free
        ?visual>
            state               free
        =retrieval>
            x                   =screen-x
            y                   =screen-y
        ?imaginal>
            state               free
        =imaginal>
    ==>
        =imaginal>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +manual>
            isa                 move-cursor
            loc                 =screen-location
        +visual>
            isa                 move-attention
            screen-pos          =screen-location

        !bind!                  =next-slot-name ("get-next-in-group-slot" =imaginal)
        =goal>
            state               preparing-retrieving-disc-ingroup-during-response
            next-group-slot     =next-slot-name
            click-state         moving-cursor
            next-disc-state     ready
    )

    (P retrieve-ingroup-disc-during-response-failure
        =goal>
            state               retrieving-next-disc-during-response
        ?retrieval>
            state               free
            buffer              failure
    ==>
        =goal>
            ; state               end
            state               preparing-root-for-next-group
    )

    (P retrieve-root-for-next-group-during-response
        =goal>
            state               preparing-root-for-next-group
            pre-root-slot       =root-slot
            pre-root-slot-value =root-slot-value
            click-state         finished
            ; next-disc-state     ready
        ?retrieval>
            state               free
    ==>
        +retrieval>
            type-tag            chunking-root
            =root-slot          =root-slot-value
        =goal>
            state               retrieving-root-during-response
    )

    (P prepare-click
        =goal>
            click-state         moving-cursor
        ?manual>
            execution           busy
    ==>
        +manual>
            isa                 prepare
            style               punch
            hand                right
            finger              index
        =goal>
            click-state         ready
    )

    (P click-on-target
        =goal>
            click-state         ready
        ?manual>
            state               free
    ==>
        +manual>
            isa                 execute
        =goal>
            click-state         finished
    )

    (P retrieve-rest-disc
        =goal>
            state               preparing-retrieve-rest-disc
    ==>
        +retrieval>
            :recently-retrieved nil
            type-tag            disc-chunk
        =goal>
            state               retrieving-rest-disc
    )

    (P move-attention-to-disc-for-checking
        =goal>
            state               retrieving-rest-disc
        ?retrieval>
            state               free
            - buffer              failure
        ?visual>
            state               free
        =retrieval>
            x                   =screen-x
            y                   =screen-y
    ==>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +visual>
            isa                 move-attention
            screen-pos          =screen-location
        =retrieval>
        =goal>
            state               checking-whether-disc-existed
    )

    (P find-disc-responded
        =goal>
            state               checking-whether-disc-existed
        ?visual>
            state               free
        =visual>
            value               "x"
    ==>
        =goal>
            state               preparing-retrieve-rest-disc
    )

    (P find-disc-not-responded
        =goal>
            state               checking-whether-disc-existed
            click-state         finished
        ?visual>
            state               free
            buffer              failure
        ?retrieval>
            state               free
        =retrieval>
            x                   =screen-x
            y                   =screen-y
        ?manual>
            state               free
    ==>
        !bind!                  =screen-location ("create-visual-location-chunk" =screen-x =screen-y)
        +manual>
            isa                 move-cursor
            loc                 =screen-location
        =goal>
            state               preparing-retrieve-rest-disc
            click-state         moving-cursor
            next-disc-state     ready
    )

    (P find-not-disc-left
        =goal>
            state               retrieving-rest-disc
        ?retrieval>
            state               free
            buffer              failure
    ==>
        =goal>
            state               end
    )
)
